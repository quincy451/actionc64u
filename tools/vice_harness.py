#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import sys
import time

API_VERSION = 0x02
STX = 0x02

CMD_MEMORY_GET = 0x01
CMD_KEYBOARD_FEED = 0x72
CMD_PING = 0x81
CMD_EXIT = 0xAA
CMD_QUIT = 0xBB

RESP_MEM_GET = 0x01
RESP_REGISTER_INFO = 0x31
RESP_JAM = 0x61
RESP_STOPPED = 0x62
RESP_RESUMED = 0x63
RESP_PING = 0x81
RESP_EXIT = 0xAA
RESP_QUIT = 0xBB


class ViceUnavailable(RuntimeError):
    pass


class ViceProtocolError(RuntimeError):
    pass


def locate_x64sc() -> Path:
    candidate = shutil.which("x64sc")
    if not candidate:
        raise ViceUnavailable("x64sc not found on PATH")
    return Path(candidate).resolve()


def default_cpm_images_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "cpm65-u64" / "images"


def find_c64_disk_image(images_dir: Path | None = None) -> Path:
    search_dir = images_dir or default_cpm_images_dir()
    if not search_dir.is_dir():
        raise ViceUnavailable(f"CP/M-65 images directory not found: {search_dir}")
    candidates = sorted(search_dir.glob("c64*.d64"))
    if not candidates:
        raise ViceUnavailable(f"no C64 CP/M disk image found under {search_dir}")
    return candidates[0].resolve()


def reserve_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def petscii_bytes(text: str) -> bytes:
    return text.replace("\n", "\r").encode("ascii", errors="strict")


def screen_code_to_ascii(code: int) -> str:
    if code in {0x00, 0x20, 0xA0}:
        return " "
    if 1 <= code <= 26:
        return chr(ord("A") + code - 1)
    if 0x30 <= code <= 0x39:
        return chr(code)
    if 0x21 <= code <= 0x2F or 0x3A <= code <= 0x3F:
        return chr(code)
    if 0x40 <= code <= 0x5A:
        return chr(code)
    return "?"


def screen_ram_to_text(data: bytes) -> str:
    if len(data) < 1000:
        raise ViceProtocolError(f"expected 1000 screen bytes, got {len(data)}")
    chars = [screen_code_to_ascii(byte) for byte in data[:1000]]
    rows = ["".join(chars[row * 40 : (row + 1) * 40]).rstrip() for row in range(25)]
    return "\n".join(rows).strip()


class BinaryMonitorClient:
    def __init__(self, host: str, port: int, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock: socket.socket | None = None
        self.request_id = 1

    def connect(self, deadline: float) -> None:
        last_error: OSError | None = None
        while time.monotonic() < deadline:
            try:
                sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
                sock.settimeout(self.timeout)
                self.sock = sock
                return
            except OSError as exc:
                last_error = exc
                time.sleep(0.2)
        raise ViceUnavailable(f"unable to connect to VICE binary monitor on {self.host}:{self.port}: {last_error}")

    def close(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            finally:
                self.sock = None

    def _recv_exact(self, length: int) -> bytes:
        if self.sock is None:
            raise ViceProtocolError("monitor socket is not connected")
        chunks = bytearray()
        while len(chunks) < length:
            part = self.sock.recv(length - len(chunks))
            if not part:
                raise ViceProtocolError("VICE monitor connection closed unexpectedly")
            chunks.extend(part)
        return bytes(chunks)

    def _read_response(self) -> tuple[int, int, int, bytes]:
        header = self._recv_exact(12)
        if header[0] != STX:
            raise ViceProtocolError(f"unexpected response prefix: 0x{header[0]:02x}")
        version = header[1]
        if version != API_VERSION:
            raise ViceProtocolError(f"unexpected VICE monitor API version: {version}")
        body_len = struct.unpack_from("<I", header, 2)[0]
        response_type = header[6]
        error_code = header[7]
        request_id = struct.unpack_from("<I", header, 8)[0]
        body = self._recv_exact(body_len) if body_len else b""
        return response_type, error_code, request_id, body

    def _send_command(self, command_type: int, body: bytes = b"") -> int:
        if self.sock is None:
            raise ViceProtocolError("monitor socket is not connected")
        request_id = self.request_id
        self.request_id += 1
        packet = bytearray()
        packet.append(STX)
        packet.append(API_VERSION)
        packet.extend(struct.pack("<I", len(body)))
        packet.extend(struct.pack("<I", request_id))
        packet.append(command_type)
        packet.extend(body)
        self.sock.sendall(packet)
        return request_id

    def command(self, command_type: int, body: bytes = b"", timeout: float | None = None) -> bytes:
        request_id = self._send_command(command_type, body)
        deadline = time.monotonic() + (timeout if timeout is not None else self.timeout)
        while time.monotonic() < deadline:
            response_type, error_code, response_request_id, payload = self._read_response()
            if response_request_id != request_id:
                continue
            if error_code != 0:
                raise ViceProtocolError(
                    f"VICE monitor command 0x{command_type:02x} failed with error 0x{error_code:02x}"
                )
            if response_type != command_type:
                raise ViceProtocolError(
                    f"VICE monitor command 0x{command_type:02x} got response 0x{response_type:02x}"
                )
            return payload
        raise ViceProtocolError(f"timed out waiting for VICE monitor response 0x{command_type:02x}")

    def ping(self) -> None:
        self.command(CMD_PING)

    def resume(self) -> None:
        self.command(CMD_EXIT)
        end = time.monotonic() + self.timeout
        while time.monotonic() < end:
            response_type, error_code, _request_id, _payload = self._read_response()
            if error_code != 0:
                raise ViceProtocolError(f"VICE monitor resume failed with error 0x{error_code:02x}")
            if response_type == RESP_RESUMED:
                return
        raise ViceProtocolError("timed out waiting for VICE resumed event")

    def quit_emulator(self) -> None:
        try:
            self.command(CMD_QUIT)
        except Exception:
            pass

    def keyboard_feed(self, text: str) -> None:
        encoded = petscii_bytes(text)
        if len(encoded) > 0xFF:
            raise ViceProtocolError("keyboard feed text is too long for a single packet")
        self.command(CMD_KEYBOARD_FEED, bytes((len(encoded),)) + encoded)
        self.resume()

    def memory_get(self, start: int, end: int, *, memspace: int = 0, bank: int = 0, side_effects: bool = False) -> bytes:
        body = bytes((1 if side_effects else 0,))
        body += struct.pack("<HHBH", start, end, memspace, bank)
        response = self.command(CMD_MEMORY_GET, body)
        if len(response) < 2:
            raise ViceProtocolError("memory-get response was too short")
        segment_len = struct.unpack_from("<H", response, 0)[0]
        data = response[2:]
        if segment_len != len(data):
            raise ViceProtocolError(f"memory-get length mismatch: header={segment_len} actual={len(data)}")
        self.resume()
        return data


class ViceHarness:
    def __init__(
        self,
        *,
        x64sc_path: Path | None = None,
        disk_image: Path | None = None,
        port: int | None = None,
        timeout: float = 8.0,
    ):
        self.x64sc_path = x64sc_path or locate_x64sc()
        self.disk_image = disk_image or find_c64_disk_image()
        self.port = port or reserve_tcp_port()
        self.timeout = timeout
        self.process: subprocess.Popen[str] | None = None
        self.monitor = BinaryMonitorClient("127.0.0.1", self.port, timeout=timeout)

    def command(self, *extra: str) -> list[str]:
        return [
            str(self.x64sc_path),
            "-default",
            "-8",
            str(self.disk_image),
            "-drive8type",
            "1541",
            "-drive8truedrive",
            "+virtualdev8",
            "-binarymonitor",
            "-binarymonitoraddress",
            f"ip4://127.0.0.1:{self.port}",
            "-reu",
            "-reusize",
            "16384",
            "-warp",
            "+sound",
            "-sounddev",
            "dummy",
            "-keybuf-delay",
            "4",
            *extra,
        ]

    def start(self) -> None:
        env = dict(os.environ)
        self.process = subprocess.Popen(
            self.command(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        deadline = time.monotonic() + 20.0
        try:
            self.monitor.connect(deadline)
            self.monitor.ping()
            self.monitor.resume()
        except Exception as exc:
            self.stop()
            raise ViceUnavailable(f"failed to start VICE monitor session: {exc}") from exc

    def stop(self) -> None:
        self.monitor.close()
        if self.process is None:
            return
        try:
            if self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        finally:
            self.process = None

    def __enter__(self) -> "ViceHarness":
        self.start()
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        self.stop()

    def read_screen_text(self) -> str:
        return screen_ram_to_text(self.monitor.memory_get(0x0400, 0x07E7))

    def feed_keys(self, text: str) -> None:
        self.monitor.keyboard_feed(text)

    def wait_for_screen_contains(self, fragment: str, *, timeout: float, poll_interval: float = 0.5) -> str:
        deadline = time.monotonic() + timeout
        last_screen = ""
        while time.monotonic() < deadline:
            if self.process is not None and self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                raise ViceUnavailable(f"x64sc exited early while waiting for screen text.\nstdout:\n{stdout}\nstderr:\n{stderr}")
            last_screen = self.read_screen_text()
            if fragment in last_screen:
                return last_screen
            time.sleep(poll_interval)
        raise ViceUnavailable(f"timed out waiting for screen text {fragment!r}; last screen was:\n{last_screen}")

    def boot_to_cpm_prompt(self, *, timeout: float = 120.0, boot_keys: str = 'LOAD"CPM",8\rRUN\r') -> str:
        self.feed_keys(boot_keys)
        return self.wait_for_screen_contains("A>", timeout=timeout)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Boot the C64 CP/M-65 image in VICE and wait for a prompt")
    parser.add_argument("--disk-image", help="explicit C64 CP/M disk image path")
    parser.add_argument("--timeout", type=float, default=120.0, help="seconds to wait for the CP/M prompt")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        harness = ViceHarness(disk_image=Path(args.disk_image) if args.disk_image else None)
    except ViceUnavailable as exc:
        print(exc, file=sys.stderr)
        return 1

    try:
        with harness as vice:
            screen = vice.boot_to_cpm_prompt(timeout=args.timeout)
    except ViceUnavailable as exc:
        print(exc, file=sys.stderr)
        return 1

    print(screen)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
