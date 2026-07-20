#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <exception>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <optional>
#include <cstdlib>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <sqlite3.h>

namespace fs = std::filesystem;

namespace {

const std::string kProjectHeader = "ACTION PROJECT";

struct ToolError : std::runtime_error {
    using std::runtime_error::runtime_error;
};

class SqliteDatabase {
public:
    explicit SqliteDatabase(const fs::path& path) {
        fs::create_directories(path.parent_path());
        const int status = sqlite3_open(path.c_str(), &database_);
        if (status != SQLITE_OK) {
            const std::string message =
                database_ == nullptr ? "open failed" : sqlite3_errmsg(database_);
            if (database_ != nullptr) {
                sqlite3_close(database_);
                database_ = nullptr;
            }
            throw ToolError("SQLITE OPEN: " + message);
        }
        exec("PRAGMA foreign_keys=ON");
    }

    SqliteDatabase(const SqliteDatabase&) = delete;
    SqliteDatabase& operator=(const SqliteDatabase&) = delete;

    ~SqliteDatabase() {
        if (database_ != nullptr) {
            sqlite3_close(database_);
        }
    }

    sqlite3* get() const {
        return database_;
    }

    void exec(const std::string& sql) {
        char* error = nullptr;
        const int status = sqlite3_exec(database_, sql.c_str(), nullptr, nullptr, &error);
        if (status != SQLITE_OK) {
            const std::string message =
                error == nullptr ? sqlite3_errmsg(database_) : error;
            sqlite3_free(error);
            throw ToolError("SQLITE EXEC: " + message);
        }
    }

private:
    sqlite3* database_ = nullptr;
};

class SqliteStatement {
public:
    SqliteStatement(SqliteDatabase& database, const std::string& sql)
        : database_(database.get()) {
        if (sqlite3_prepare_v2(database_, sql.c_str(), -1, &statement_, nullptr) !=
            SQLITE_OK) {
            throw ToolError("SQLITE PREPARE: " + std::string(sqlite3_errmsg(database_)));
        }
    }

    SqliteStatement(const SqliteStatement&) = delete;
    SqliteStatement& operator=(const SqliteStatement&) = delete;

    ~SqliteStatement() {
        if (statement_ != nullptr) {
            sqlite3_finalize(statement_);
        }
    }

    void bind_text(int index, std::string_view value) {
        if (sqlite3_bind_text64(
                statement_,
                index,
                value.data(),
                static_cast<sqlite3_uint64>(value.size()),
                SQLITE_TRANSIENT,
                SQLITE_UTF8) != SQLITE_OK) {
            throw ToolError("SQLITE BIND: " + std::string(sqlite3_errmsg(database_)));
        }
    }

    void bind_integer(int index, std::int64_t value) {
        if (sqlite3_bind_int64(statement_, index, value) != SQLITE_OK) {
            throw ToolError("SQLITE BIND: " + std::string(sqlite3_errmsg(database_)));
        }
    }

    bool step() {
        const int status = sqlite3_step(statement_);
        if (status == SQLITE_ROW) {
            return true;
        }
        if (status == SQLITE_DONE) {
            return false;
        }
        throw ToolError("SQLITE STEP: " + std::string(sqlite3_errmsg(database_)));
    }

    void reset() {
        if (sqlite3_reset(statement_) != SQLITE_OK ||
            sqlite3_clear_bindings(statement_) != SQLITE_OK) {
            throw ToolError("SQLITE RESET: " + std::string(sqlite3_errmsg(database_)));
        }
    }

    std::int64_t integer(int column) const {
        return sqlite3_column_int64(statement_, column);
    }

    std::string text(int column) const {
        const unsigned char* value = sqlite3_column_text(statement_, column);
        return value == nullptr
            ? std::string{}
            : std::string(reinterpret_cast<const char*>(value));
    }

private:
    sqlite3* database_ = nullptr;
    sqlite3_stmt* statement_ = nullptr;
};

std::string upper_ascii(std::string_view input) {
    std::string out;
    out.reserve(input.size());
    for (unsigned char ch : input) {
        out.push_back(static_cast<char>(std::toupper(ch)));
    }
    return out;
}

std::string trim(std::string_view input) {
    std::size_t first = 0;
    while (first < input.size() && std::isspace(static_cast<unsigned char>(input[first]))) {
        ++first;
    }
    std::size_t last = input.size();
    while (last > first && std::isspace(static_cast<unsigned char>(input[last - 1]))) {
        --last;
    }
    return std::string(input.substr(first, last - first));
}

std::vector<std::string> split_lines(const std::string& text) {
    std::vector<std::string> lines;
    std::string current;
    for (char ch : text) {
        if (ch == '\r' || ch == '\n') {
            lines.push_back(current);
            current.clear();
            continue;
        }
        current.push_back(ch);
    }
    if (!current.empty() || text.empty()) {
        lines.push_back(current);
    }
    return lines;
}

std::string strip_source_comment(std::string_view line) {
    bool in_string = false;
    bool escaped = false;
    for (std::size_t i = 0; i < line.size(); ++i) {
        const char ch = line[i];
        if (in_string && ch == '\\' && !escaped) {
            escaped = true;
            continue;
        }
        if (ch == '"' && !escaped) {
            in_string = !in_string;
        } else if (ch == ';' && !in_string) {
            return std::string(line.substr(0, i));
        }
        escaped = false;
    }
    return std::string(line);
}

std::string join_lines(const std::vector<std::string>& lines) {
    std::string text;
    for (const std::string& line : lines) {
        text += line;
        text += "\n";
    }
    return text;
}

std::string read_text_file(const fs::path& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        throw ToolError("LOAD FAIL");
    }
    return std::string(std::istreambuf_iterator<char>(in), std::istreambuf_iterator<char>());
}

void write_text_file(const fs::path& path, std::string_view text) {
    if (!path.parent_path().empty()) {
        fs::create_directories(path.parent_path());
    }
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) {
        throw ToolError("SAVE FAIL");
    }
    out.write(text.data(), static_cast<std::streamsize>(text.size()));
    if (!out) {
        throw ToolError("SAVE FAIL");
    }
}

void write_binary_file(const fs::path& path, const std::vector<std::uint8_t>& bytes) {
    if (!path.parent_path().empty()) {
        fs::create_directories(path.parent_path());
    }
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) {
        throw ToolError("SAVE FAIL");
    }
    out.write(reinterpret_cast<const char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
    if (!out) {
        throw ToolError("SAVE FAIL");
    }
}

std::optional<fs::path> child_case_insensitive(const fs::path& directory, std::string_view wanted) {
    if (!fs::is_directory(directory)) {
        return std::nullopt;
    }
    const std::string wanted_upper = upper_ascii(wanted);
    for (const auto& entry : fs::directory_iterator(directory)) {
        if (upper_ascii(entry.path().filename().string()) == wanted_upper) {
            return entry.path();
        }
    }
    return std::nullopt;
}

fs::path required_child_ci(const fs::path& directory, std::string_view wanted, std::string_view error) {
    auto found = child_case_insensitive(directory, wanted);
    if (!found) {
        throw ToolError(std::string(error));
    }
    return *found;
}

fs::path project_manifest_path(const fs::path& root) {
    return required_child_ci(root, "ACTION.PROJ", "NO PROJECT");
}

std::string module_from_arg(std::string_view arg) {
    std::string value = trim(arg);
    if (value.empty()) {
        throw ToolError("NO NAME");
    }
    for (char& ch : value) {
        if (ch == '\\') {
            ch = '/';
        }
    }
    fs::path p(value);
    std::string name = p.filename().string();
    const std::string suffix = ".ACT";
    if (name.size() >= suffix.size() &&
        upper_ascii(std::string_view(name).substr(name.size() - suffix.size())) == suffix) {
        name.resize(name.size() - suffix.size());
    }
    name = upper_ascii(name);
    if (name.empty()) {
        throw ToolError("BAD NAME");
    }
    const bool ok = std::all_of(name.begin(), name.end(), [](unsigned char ch) {
        return std::isalnum(ch) || ch == '_';
    });
    if (!ok) {
        throw ToolError("BAD NAME");
    }
    return name;
}

std::vector<std::string> load_manifest_entries(const fs::path& root) {
    const std::string text = read_text_file(project_manifest_path(root));
    std::vector<std::string> raw = split_lines(text);
    std::vector<std::string> entries;
    bool saw_header = false;
    for (const std::string& line : raw) {
        std::string cleaned = trim(line);
        if (cleaned.empty()) {
            continue;
        }
        if (!saw_header) {
            if (upper_ascii(cleaned) != kProjectHeader) {
                throw ToolError("NO PROJECT");
            }
            saw_header = true;
            continue;
        }
        entries.push_back(upper_ascii(cleaned));
    }
    if (!saw_header) {
        throw ToolError("NO PROJECT");
    }
    return entries;
}

void save_manifest_entries(const fs::path& root, const std::vector<std::string>& entries) {
    std::string text = kProjectHeader + "\n";
    for (const std::string& entry : entries) {
        text += upper_ascii(entry) + "\n";
    }
    write_text_file(root / "ACTION.PROJ", text);
}

bool manifest_contains_module(const std::vector<std::string>& entries, const std::string& module) {
    const std::string wanted = upper_ascii(module) + ".ACT";
    return std::any_of(entries.begin(), entries.end(), [&](const std::string& entry) {
        return upper_ascii(entry) == wanted;
    });
}

fs::path project_dir(const fs::path& root, std::string_view name) {
    auto found = child_case_insensitive(root, name);
    if (found && fs::is_directory(*found)) {
        return *found;
    }
    return root / std::string(name);
}

fs::path source_path(const fs::path& root, const std::string& module) {
    const fs::path src = project_dir(root, "SRC");
    auto found = child_case_insensitive(src, module + ".ACT");
    return found.value_or(src / (module + ".ACT"));
}

fs::path object_path(const fs::path& root, const std::string& module) {
    const fs::path obj = project_dir(root, "OBJ");
    auto found = child_case_insensitive(obj, module + ".OBJ");
    return found.value_or(obj / (module + ".OBJ"));
}

fs::path binary_path(const fs::path& root, const std::string& module) {
    return project_dir(root, "BIN") / (module + ".PRG");
}

fs::path debug_path(const fs::path& root, const std::string& module) {
    return project_dir(root, "BIN") / (module + ".DBG");
}

void require_project_module(const fs::path& root, const std::string& module) {
    const auto entries = load_manifest_entries(root);
    if (!manifest_contains_module(entries, module)) {
        throw ToolError("NOT IN PROJECT");
    }
}

std::vector<std::string> read_source_lines(const fs::path& path) {
    if (!fs::is_regular_file(path)) {
        throw ToolError("NO FILE");
    }
    std::string text = read_text_file(path);
    std::vector<std::string> lines = split_lines(text);
    if (!lines.empty() && lines.back().empty()) {
        lines.pop_back();
    }
    return lines;
}

std::size_t parse_one_based_line(const std::string& text, std::size_t max_inclusive) {
    std::size_t pos = 0;
    const unsigned long value = std::stoul(text, &pos, 10);
    if (pos != text.size() || value == 0 || value > max_inclusive) {
        throw ToolError("BAD LINE");
    }
    return static_cast<std::size_t>(value - 1);
}

std::string shell_quote(const fs::path& path) {
    std::string input = path.string();
    std::string quoted = "'";
    for (char ch : input) {
        if (ch == '\'') {
            quoted += "'\\''";
        } else {
            quoted.push_back(ch);
        }
    }
    quoted += "'";
    return quoted;
}

std::string bytes_to_hex(const std::vector<std::uint8_t>& bytes) {
    std::ostringstream out;
    out << std::uppercase << std::hex << std::setfill('0');
    for (std::uint8_t byte : bytes) {
        out << std::setw(2) << static_cast<int>(byte);
    }
    return out.str();
}

std::vector<std::uint8_t> hex_to_bytes(std::string_view hex) {
    std::vector<std::uint8_t> bytes;
    std::string compact;
    compact.reserve(hex.size());
    for (char ch : hex) {
        if (!std::isspace(static_cast<unsigned char>(ch))) {
            compact.push_back(ch);
        }
    }
    if (compact.size() % 2 != 0) {
        throw ToolError("BAD OBJECT");
    }
    bytes.reserve(compact.size() / 2);
    for (std::size_t i = 0; i < compact.size(); i += 2) {
        const std::string pair = compact.substr(i, 2);
        bytes.push_back(static_cast<std::uint8_t>(std::stoul(pair, nullptr, 16)));
    }
    return bytes;
}

std::vector<std::string> split_words(std::string_view line) {
    std::istringstream in{std::string(line)};
    std::vector<std::string> words;
    std::string word;
    while (in >> word) {
        words.push_back(word);
    }
    return words;
}

struct SourceParameter {
    std::string name;
    std::string type;
    bool is_array = false;
    bool is_pointer = false;
};

std::optional<std::string> proc_name_from_line(const std::string& line) {
    const std::string cleaned = trim(line);
    const std::string upper = upper_ascii(cleaned);
    if (upper.rfind("PROC ", 0) != 0) {
        return std::nullopt;
    }
    std::string rest = trim(cleaned.substr(5));
    const std::size_t paren = rest.find('(');
    if (paren != std::string::npos) {
        rest.resize(paren);
    }
    rest = trim(rest);
    if (rest.empty()) {
        throw ToolError("BAD PROC");
    }
    return module_from_arg(rest);
}

std::optional<std::string> call_name_from_line(const std::string& line) {
    std::string cleaned = trim(line);
    if (cleaned.empty()) {
        return std::nullopt;
    }
    const std::string upper = upper_ascii(cleaned);
    if (upper.rfind("RETURN", 0) == 0 || upper == "ENDPROC" ||
        upper == "ENDFUNC" || upper.rfind("PROC ", 0) == 0 ||
        upper.rfind("MODULE ", 0) == 0) {
        return std::nullopt;
    }
    const std::size_t paren = cleaned.find('(');
    if (paren == std::string::npos) {
        return std::nullopt;
    }
    std::string name = trim(cleaned.substr(0, paren));
    if (name.empty()) {
        return std::nullopt;
    }
    if (name.find('=') != std::string::npos || name.find(' ') != std::string::npos) {
        return std::nullopt;
    }
    return module_from_arg(name);
}

std::vector<std::string> split_call_arguments(std::string_view text) {
    std::vector<std::string> arguments;
    std::size_t start = 0;
    int depth = 0;
    bool in_string = false;
    for (std::size_t i = 0; i < text.size(); ++i) {
        const char ch = text[i];
        if (ch == '"') {
            in_string = !in_string;
        } else if (!in_string && ch == '(') {
            ++depth;
        } else if (!in_string && ch == ')') {
            --depth;
            if (depth < 0) {
                throw ToolError("BAD CALL");
            }
        } else if (!in_string && depth == 0 && ch == ',') {
            std::string argument = trim(text.substr(start, i - start));
            if (argument.empty()) {
                throw ToolError("BAD CALL");
            }
            arguments.push_back(std::move(argument));
            start = i + 1;
        }
    }
    if (depth != 0 || in_string) {
        throw ToolError("BAD CALL");
    }
    std::string final_argument = trim(text.substr(start));
    if (!final_argument.empty()) {
        arguments.push_back(std::move(final_argument));
    } else if (!arguments.empty()) {
        throw ToolError("BAD CALL");
    }
    return arguments;
}

std::vector<SourceParameter> proc_parameters_from_line(const std::string& line) {
    const std::string cleaned = trim(line);
    const std::size_t open = cleaned.find('(');
    const std::size_t close = cleaned.rfind(')');
    if (open == std::string::npos || close == std::string::npos || close < open ||
        !trim(std::string_view(cleaned).substr(close + 1)).empty()) {
        throw ToolError("BAD PROC");
    }
    const std::string body = trim(
        std::string_view(cleaned).substr(open + 1, close - open - 1));
    if (body.empty()) {
        return {};
    }

    std::vector<SourceParameter> parameters;
    std::string current_type;
    bool current_array = false;
    bool current_pointer = false;
    for (std::string item : split_call_arguments(body)) {
        item = trim(item);
        const std::string upper = upper_ascii(item);
        bool supplied_type = false;
        for (const std::string type : {"BYTE", "CARD", "INT", "REAL"}) {
            const std::string array_prefix = type + " ARRAY ";
            const std::string pointer_prefix = type + " POINTER ";
            const std::string scalar_prefix = type + " ";
            if (upper.rfind(array_prefix, 0) == 0) {
                current_type = type;
                current_array = true;
                current_pointer = false;
                item = trim(std::string_view(item).substr(array_prefix.size()));
                supplied_type = true;
                break;
            }
            if (upper.rfind(pointer_prefix, 0) == 0) {
                current_type = type;
                current_array = false;
                current_pointer = true;
                item = trim(std::string_view(item).substr(pointer_prefix.size()));
                supplied_type = true;
                break;
            }
            if (upper.rfind(scalar_prefix, 0) == 0) {
                current_type = type;
                current_array = false;
                current_pointer = false;
                item = trim(std::string_view(item).substr(scalar_prefix.size()));
                supplied_type = true;
                break;
            }
        }
        if (!supplied_type && current_type.empty()) {
            throw ToolError("BAD PROC PARAM");
        }
        if (item.empty() || item.find_first_not_of(
                                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_") !=
                                std::string::npos ||
            std::isdigit(static_cast<unsigned char>(item.front()))) {
            throw ToolError("BAD PROC PARAM");
        }
        parameters.push_back(SourceParameter{
            module_from_arg(item),
            current_type,
            current_array,
            current_pointer,
        });
    }
    return parameters;
}

struct ParsedFunctionDeclaration {
    std::string name;
    std::string return_type;
    std::vector<SourceParameter> parameters;
};

std::optional<ParsedFunctionDeclaration> function_from_line(
    const std::string& line) {
    static const std::regex declaration(
        R"(^\s*(BYTE|CARD|INT|REAL)\s+FUNC\s+([A-Za-z_][A-Za-z0-9_]*)\s*(\(.*\))\s*$)",
        std::regex_constants::icase);
    std::smatch match;
    if (!std::regex_match(line, match, declaration)) {
        return std::nullopt;
    }
    return ParsedFunctionDeclaration{
        module_from_arg(match[2].str()),
        upper_ascii(match[1].str()),
        proc_parameters_from_line(line),
    };
}

struct ParsedCall {
    std::string name;
    std::vector<std::string> arguments;
};

std::optional<ParsedCall> parse_call_expression(std::string_view text) {
    const std::string cleaned = trim(text);
    const std::size_t open = cleaned.find('(');
    const std::size_t close = cleaned.rfind(')');
    if (open == std::string::npos || close == std::string::npos || close != cleaned.size() - 1 ||
        close < open) {
        return std::nullopt;
    }
    int depth = 0;
    bool in_string = false;
    bool escaped = false;
    for (std::size_t i = open; i <= close; ++i) {
        const char ch = cleaned[i];
        if (in_string && ch == '\\' && !escaped) {
            escaped = true;
            continue;
        }
        if (ch == '"' && !escaped) {
            in_string = !in_string;
        } else if (!in_string && ch == '(') {
            ++depth;
        } else if (!in_string && ch == ')') {
            --depth;
            if (depth < 0 || (depth == 0 && i != close)) {
                return std::nullopt;
            }
        }
        escaped = false;
    }
    if (depth != 0 || in_string) {
        return std::nullopt;
    }
    const std::string name = trim(std::string_view(cleaned).substr(0, open));
    if (name.empty() || name.find_first_not_of(
                            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_") !=
                            std::string::npos) {
        return std::nullopt;
    }
    return ParsedCall{
        module_from_arg(name),
        split_call_arguments(std::string_view(cleaned).substr(open + 1, close - open - 1)),
    };
}

std::optional<std::string> print_string_from_line(const std::string& line) {
    const std::string cleaned = trim(line);
    const std::string upper = upper_ascii(cleaned);
    if (upper.rfind("PRINTE", 0) != 0) {
        return std::nullopt;
    }
    const std::size_t open = cleaned.find('"');
    const std::size_t close = cleaned.rfind('"');
    if (open == std::string::npos || close == std::string::npos) {
        return std::nullopt;
    }
    if (close <= open) {
        throw ToolError("BAD PRINT");
    }
    std::string out;
    for (std::size_t i = open + 1; i < close; ++i) {
        if (cleaned[i] == '\\' && i + 1 < close) {
            ++i;
            if (cleaned[i] == 'n') {
                out.push_back('\n');
            } else if (cleaned[i] == 'r') {
                out.push_back('\r');
            } else {
                out.push_back(cleaned[i]);
            }
        } else {
            out.push_back(cleaned[i]);
        }
    }
    return out;
}

std::optional<std::string> print_string_expr_from_line(const std::string& line) {
    const std::string cleaned = trim(line);
    const std::string upper = upper_ascii(cleaned);
    if (upper.rfind("PRINTE", 0) != 0) {
        return std::nullopt;
    }
    const std::size_t open = cleaned.find('(');
    const std::size_t close = cleaned.rfind(')');
    if (open == std::string::npos || close != cleaned.size() - 1 || close <= open) {
        throw ToolError("BAD PRINT");
    }
    const std::string expression = trim(
        std::string_view(cleaned).substr(open + 1, close - open - 1));
    if (expression.empty()) {
        throw ToolError("BAD PRINT");
    }
    return expression;
}

std::optional<std::string> print_int_expr_from_line(const std::string& line) {
    const std::string cleaned = trim(line);
    const std::string upper = upper_ascii(cleaned);
    if (upper.rfind("PRINTIE", 0) != 0) {
        return std::nullopt;
    }
    const std::size_t open = cleaned.find('(');
    const std::size_t close = cleaned.rfind(')');
    if (open == std::string::npos || close == std::string::npos || close <= open) {
        throw ToolError("BAD PRINT");
    }
    return trim(std::string_view(cleaned).substr(open + 1, close - open - 1));
}

std::optional<std::string> print_int_call_from_line(const std::string& line) {
    const std::string cleaned = trim(line);
    const std::string upper = upper_ascii(cleaned);
    if (upper.rfind("PRINTI", 0) != 0 || upper.rfind("PRINTIE", 0) == 0) {
        return std::nullopt;
    }
    const std::size_t open = cleaned.find('(');
    const std::size_t close = cleaned.rfind(')');
    if (open == std::string::npos || close == std::string::npos || close <= open) {
        throw ToolError("BAD PRINT");
    }
    return trim(std::string_view(cleaned).substr(open + 1, close - open - 1));
}

std::optional<std::pair<std::string, bool>> print_real_expr_from_line(
    const std::string& line) {
    const std::string cleaned = trim(line);
    const std::string upper = upper_ascii(cleaned);
    bool newline = false;
    if (upper.rfind("PRINTRE", 0) == 0) {
        newline = true;
    } else if (upper.rfind("PRINTR", 0) != 0) {
        return std::nullopt;
    }
    const std::size_t open = cleaned.find('(');
    const std::size_t close = cleaned.rfind(')');
    if (open == std::string::npos || close != cleaned.size() - 1 || close <= open) {
        throw ToolError("BAD REAL PRINT");
    }
    const std::string expression = trim(
        std::string_view(cleaned).substr(open + 1, close - open - 1));
    if (expression.empty()) {
        throw ToolError("BAD REAL PRINT");
    }
    return std::make_pair(expression, newline);
}

struct ParsedDeclaration {
    std::string name;
    std::string type;
    std::string mode;
    std::string expression;
};

struct ParsedArrayDeclaration {
    std::string name;
    std::string type;
    std::string size_expression;
    std::string mode;
    std::string expression;
};

struct ParsedReuDeclaration {
    std::string name;
    std::string size_expression;
};

std::optional<ParsedReuDeclaration> reu_declaration_from_line(const std::string& line) {
    static const std::regex declaration(
        R"(^\s*REU\s+BYTE\s+ARRAY\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.+)\)\s*$)",
        std::regex_constants::icase);
    std::smatch match;
    if (!std::regex_match(line, match, declaration)) {
        return std::nullopt;
    }
    const std::string size_expression = trim(match[2].str());
    if (size_expression.empty()) {
        throw ToolError("BAD REU DECL");
    }
    return ParsedReuDeclaration{
        module_from_arg(match[1].str()),
        size_expression,
    };
}

std::vector<std::string> split_declarators(std::string_view text) {
    std::vector<std::string> items;
    std::size_t start = 0;
    int paren_depth = 0;
    int bracket_depth = 0;
    bool in_string = false;
    bool escaped = false;
    for (std::size_t i = 0; i < text.size(); ++i) {
        const char ch = text[i];
        if (in_string) {
            if (escaped) {
                escaped = false;
            } else if (ch == '\\') {
                escaped = true;
            } else if (ch == '"') {
                in_string = false;
            }
            continue;
        }
        if (ch == '"') {
            in_string = true;
        } else if (ch == '(') {
            ++paren_depth;
        } else if (ch == ')') {
            --paren_depth;
        } else if (ch == '[') {
            ++bracket_depth;
        } else if (ch == ']') {
            --bracket_depth;
        } else if (ch == ',' && paren_depth == 0 && bracket_depth == 0) {
            const std::string item = trim(text.substr(start, i - start));
            if (item.empty()) {
                throw ToolError("BAD DECL");
            }
            items.push_back(item);
            start = i + 1;
        }
        if (paren_depth < 0 || bracket_depth < 0) {
            throw ToolError("BAD DECL");
        }
    }
    if (in_string || paren_depth != 0 || bracket_depth != 0) {
        throw ToolError("BAD DECL");
    }
    const std::string final_item = trim(text.substr(start));
    if (final_item.empty()) {
        throw ToolError("BAD DECL");
    }
    items.push_back(final_item);
    return items;
}

std::vector<ParsedArrayDeclaration> array_declarations_from_line(
    const std::string& line) {
    const std::string cleaned = trim(line);
    const std::string upper = upper_ascii(cleaned);
    std::string type;
    std::string rest;
    for (const std::string candidate : {"BYTE", "CARD", "INT", "REAL"}) {
        const std::string prefix = candidate + " ARRAY ";
        if (upper.rfind(prefix, 0) == 0) {
            type = candidate;
            rest = trim(std::string_view(cleaned).substr(prefix.size()));
            break;
        }
    }
    if (type.empty()) {
        return {};
    }

    std::vector<ParsedArrayDeclaration> declarations;
    for (const std::string& declarator : split_declarators(rest)) {
        std::size_t pos = 0;
        while (pos < declarator.size() &&
               (std::isalnum(static_cast<unsigned char>(declarator[pos])) ||
                declarator[pos] == '_')) {
            ++pos;
        }
        const std::string name = declarator.substr(0, pos);
        if (name.empty() || std::isdigit(static_cast<unsigned char>(name.front()))) {
            throw ToolError("BAD ARRAY DECL");
        }
        while (pos < declarator.size() &&
               std::isspace(static_cast<unsigned char>(declarator[pos]))) {
            ++pos;
        }

        std::string size_expression;
        if (pos < declarator.size() && declarator[pos] == '(') {
            const std::size_t close = declarator.find(')', pos + 1);
            if (close == std::string::npos) {
                throw ToolError("BAD ARRAY DECL");
            }
            size_expression = trim(std::string_view(declarator).substr(
                pos + 1, close - pos - 1));
            if (size_expression.empty()) {
                throw ToolError("BAD ARRAY DECL");
            }
            pos = close + 1;
            while (pos < declarator.size() &&
                   std::isspace(static_cast<unsigned char>(declarator[pos]))) {
                ++pos;
            }
        }

        std::string mode = size_expression.empty() ? "POINTER" : "STORAGE";
        std::string expression;
        if (pos < declarator.size()) {
            if (declarator[pos] != '=') {
                throw ToolError("BAD ARRAY DECL");
            }
            expression = trim(std::string_view(declarator).substr(pos + 1));
            if (expression.empty()) {
                throw ToolError("BAD ARRAY DECL");
            }
            if (expression.front() == '"' && expression.back() == '"') {
                mode = "STRING";
            } else if (expression.front() == '[' && expression.back() == ']') {
                mode = "VALUES";
                expression = trim(std::string_view(expression).substr(
                    1, expression.size() - 2));
            } else {
                mode = "ADDRESS";
            }
        }
        declarations.push_back(ParsedArrayDeclaration{
            module_from_arg(name),
            type,
            size_expression,
            mode,
            expression,
        });
    }
    return declarations;
}

std::vector<ParsedDeclaration> declarations_from_line(const std::string& line) {
    const std::string cleaned = trim(line);
    const std::string upper = upper_ascii(cleaned);
    std::string type;
    std::string rest;
    if (upper.rfind("BYTE ", 0) == 0) {
        type = "BYTE";
        rest = trim(cleaned.substr(5));
    } else if (upper.rfind("CARD ", 0) == 0) {
        type = "CARD";
        rest = trim(cleaned.substr(5));
    } else if (upper.rfind("REAL ", 0) == 0) {
        type = "REAL";
        rest = trim(cleaned.substr(5));
    } else if (upper.rfind("INT ", 0) == 0) {
        type = "INT";
        rest = trim(cleaned.substr(4));
    } else {
        return {};
    }
    const std::string upper_rest = upper_ascii(rest);
    if (upper_rest.rfind("ARRAY ", 0) == 0) {
        return {};
    }
    const bool pointer = upper_rest.rfind("POINTER ", 0) == 0;
    if (pointer) {
        type += "_POINTER";
        rest = trim(std::string_view(rest).substr(8));
    }

    std::vector<ParsedDeclaration> declarations;
    std::size_t start = 0;
    while (start < rest.size()) {
        const std::size_t comma = rest.find(',', start);
        std::string declarator = trim(std::string_view(rest).substr(
            start, comma == std::string::npos ? std::string::npos : comma - start));
        const std::size_t equals = declarator.find('=');
        std::string name = trim(std::string_view(declarator).substr(0, equals));
        std::string mode = "STORAGE";
        std::string expression;
        if (equals != std::string::npos) {
            expression = trim(std::string_view(declarator).substr(equals + 1));
            if (!pointer && expression.size() >= 2 && expression.front() == '[' && expression.back() == ']') {
                mode = "INITIAL";
                expression = trim(
                    std::string_view(expression).substr(1, expression.size() - 2));
            } else {
                mode = pointer ? "INITIAL" : "ADDRESS";
            }
        }
        if (name.empty() || (mode != "STORAGE" && expression.empty())) {
            throw ToolError("BAD DECL");
        }
        declarations.push_back(ParsedDeclaration{
            module_from_arg(name),
            type,
            mode,
            expression,
        });
        if (comma == std::string::npos) {
            break;
        }
        start = comma + 1;
    }
    if (declarations.empty()) {
        throw ToolError("BAD DECL");
    }
    return declarations;
}

struct ParsedAssignment {
    std::string name;
    std::string expression;
    std::string mode;
    std::string index_expression;
};

std::optional<ParsedAssignment> assignment_from_line(const std::string& line) {
    const std::string cleaned = trim(line);
    const std::size_t equals = cleaned.find('=');
    if (equals == std::string::npos) {
        return std::nullopt;
    }
    std::string name = trim(std::string_view(cleaned).substr(0, equals));
    std::string expr = trim(std::string_view(cleaned).substr(equals + 1));
    if (name.empty() || expr.empty()) {
        return std::nullopt;
    }
    if (name.back() == '^') {
        const std::string pointer_name = trim(
            std::string_view(name).substr(0, name.size() - 1));
        return ParsedAssignment{
            module_from_arg(pointer_name),
            expr,
            "DEREFERENCE",
            {},
        };
    }
    if (auto indexed = parse_call_expression(name)) {
        if (indexed->arguments.size() != 1) {
            throw ToolError("BAD ARRAY ASSIGN");
        }
        return ParsedAssignment{
            indexed->name,
            expr,
            "INDEX",
            indexed->arguments.front(),
        };
    }
    if (name.find(' ') != std::string::npos) {
        return std::nullopt;
    }
    return ParsedAssignment{module_from_arg(name), expr, "VARIABLE", {}};
}

std::optional<std::string> conditional_expr_from_line(
    const std::string& line,
    std::string_view keyword,
    bool requires_then) {
    const std::string cleaned = trim(line);
    const std::string upper = upper_ascii(cleaned);
    const std::string prefix = upper_ascii(keyword) + " ";
    if (upper.rfind(prefix, 0) != 0) {
        return std::nullopt;
    }
    if (!requires_then) {
        const std::string expression = trim(
            std::string_view(cleaned).substr(prefix.size()));
        if (expression.empty()) {
            throw ToolError("BAD CONDITION");
        }
        return expression;
    }
    const std::string marker = " THEN";
    const std::size_t then_pos = upper.rfind(marker);
    if (then_pos == std::string::npos || then_pos < prefix.size()) {
        throw ToolError("BAD IF");
    }
    const std::string expression = trim(
        std::string_view(cleaned).substr(prefix.size(), then_pos - prefix.size()));
    if (expression.empty()) {
        throw ToolError("BAD IF");
    }
    return expression;
}

struct ParsedForClause {
    std::string counter;
    std::string initial;
    std::string final_value;
    std::string step;
};

std::optional<std::size_t> find_top_level_word(
    std::string_view text,
    std::string_view word) {
    const std::string upper = upper_ascii(text);
    const std::string wanted = upper_ascii(word);
    int depth = 0;
    for (std::size_t i = 0; i + wanted.size() <= upper.size(); ++i) {
        if (upper[i] == '(') {
            ++depth;
            continue;
        }
        if (upper[i] == ')') {
            --depth;
            if (depth < 0) {
                throw ToolError("BAD FOR");
            }
            continue;
        }
        if (depth != 0 || upper.compare(i, wanted.size(), wanted) != 0) {
            continue;
        }
        const bool before_ok =
            i == 0 || std::isspace(static_cast<unsigned char>(upper[i - 1]));
        const std::size_t after = i + wanted.size();
        const bool after_ok =
            after == upper.size() || std::isspace(static_cast<unsigned char>(upper[after]));
        if (before_ok && after_ok) {
            return i;
        }
    }
    if (depth != 0) {
        throw ToolError("BAD FOR");
    }
    return std::nullopt;
}

std::optional<ParsedForClause> for_clause_from_line(const std::string& line) {
    const std::string cleaned = trim(line);
    const std::string upper = upper_ascii(cleaned);
    if (upper.rfind("FOR ", 0) != 0) {
        return std::nullopt;
    }
    const std::string clause = trim(std::string_view(cleaned).substr(4));
    const std::size_t equals = clause.find('=');
    if (equals == std::string::npos) {
        throw ToolError("BAD FOR");
    }
    const std::string counter = trim(std::string_view(clause).substr(0, equals));
    const std::string values = trim(std::string_view(clause).substr(equals + 1));
    const auto to_pos = find_top_level_word(values, "TO");
    if (!to_pos || counter.empty() ||
        counter.find_first_not_of(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_") != std::string::npos) {
        throw ToolError("BAD FOR");
    }
    const std::string initial = trim(std::string_view(values).substr(0, *to_pos));
    const std::string final_and_step = trim(
        std::string_view(values).substr(*to_pos + 2));
    const auto step_pos = find_top_level_word(final_and_step, "STEP");
    const std::string final_value = trim(std::string_view(final_and_step).substr(
        0, step_pos ? *step_pos : std::string::npos));
    const std::string step = step_pos
        ? trim(std::string_view(final_and_step).substr(*step_pos + 4))
        : "1";
    if (initial.empty() || final_value.empty() || step.empty()) {
        throw ToolError("BAD FOR");
    }
    return ParsedForClause{module_from_arg(counter), initial, final_value, step};
}

struct SourceOp {
    enum class Kind {
        Call,
        Return,
        Print,
        PrintString,
        PrintInt,
        PrintIntCall,
        PrintReal,
        Assign,
        Declare,
        ArrayDeclare,
        ReuDeclare,
        If,
        ElseIf,
        Else,
        Fi,
        For,
        While,
        Do,
        Until,
        Od,
        Exit,
    };
    Kind kind = Kind::Call;
    std::string value;
    std::string aux;
    std::size_t line = 0;
    std::string mode;
    std::string expression;
    std::string size_expression;

    SourceOp() = default;
    SourceOp(
        Kind source_kind,
        std::string source_value,
        std::string source_aux,
        std::size_t source_line,
        std::string source_mode = {},
        std::string source_expression = {},
        std::string source_size_expression = {})
        : kind(source_kind),
          value(std::move(source_value)),
          aux(std::move(source_aux)),
          line(source_line),
          mode(std::move(source_mode)),
          expression(std::move(source_expression)),
          size_expression(std::move(source_size_expression)) {}
};

struct SourceProc {
    std::string name;
    std::vector<SourceParameter> parameters;
    std::vector<SourceOp> ops;
    std::size_t line = 0;
    bool is_overlay = false;
    std::string return_type;
};

struct SourceGlobal {
    std::string name;
    std::string type;
    std::size_t line = 0;
    std::string mode;
    std::string expression;
    std::string size_expression;
};

struct ParsedSource {
    std::vector<SourceGlobal> globals;
    std::vector<SourceProc> procs;
};

ParsedSource parse_source(const std::string& text) {
    ParsedSource source;
    std::optional<std::size_t> current;
    const auto lines = split_lines(text);
    for (std::size_t i = 0; i < lines.size(); ++i) {
        const std::string line = strip_source_comment(lines[i]);
        const std::string cleaned = trim(line);
        const std::string upper = upper_ascii(cleaned);
        if (cleaned.empty()) {
            continue;
        }
        if (upper.rfind("OVERLAY ", 0) == 0) {
            if (current) {
                throw ToolError(
                    "NESTED OVERLAY LINE " + std::to_string(i + 1));
            }
            const std::string name = trim(std::string_view(cleaned).substr(8));
            if (name.empty() ||
                name.find_first_not_of(
                    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_") !=
                    std::string::npos) {
                throw ToolError("BAD OVERLAY LINE " + std::to_string(i + 1));
            }
            source.procs.push_back(SourceProc{
                module_from_arg(name),
                {},
                {},
                i + 1,
                true,
                {},
            });
            current = source.procs.size() - 1;
            continue;
        }
        if (auto proc = proc_name_from_line(line)) {
            source.procs.push_back(SourceProc{
                *proc,
                proc_parameters_from_line(line),
                {},
                i + 1,
                false,
                {},
            });
            current = source.procs.size() - 1;
            continue;
        }
        if (auto function = function_from_line(line)) {
            source.procs.push_back(SourceProc{
                function->name,
                std::move(function->parameters),
                {},
                i + 1,
                false,
                function->return_type,
            });
            current = source.procs.size() - 1;
            continue;
        }
        if (upper == "ENDPROC" || upper == "ENDFUNC" || upper == "ENDOVERLAY") {
            current = std::nullopt;
            continue;
        }
        if (current) {
            if (upper == "RETURN") {
                source.procs[*current].ops.push_back(
                    SourceOp{SourceOp::Kind::Return, {}, {}, i + 1});
                continue;
            }
            if (upper.rfind("RETURN", 0) == 0 && upper.size() > 6 &&
                (cleaned[6] == '(' ||
                 std::isspace(static_cast<unsigned char>(cleaned[6])))) {
                const std::string result = trim(std::string_view(cleaned).substr(6));
                if (result.size() < 3 || result.front() != '(' ||
                    result.back() != ')' ||
                    trim(std::string_view(result).substr(1, result.size() - 2)).empty()) {
                    throw ToolError(
                        "BAD RETURN LINE " + std::to_string(i + 1));
                }
                source.procs[*current].ops.push_back(SourceOp{
                    SourceOp::Kind::Return,
                    trim(std::string_view(result).substr(1, result.size() - 2)),
                    {},
                    i + 1,
                });
            } else if (auto expr = conditional_expr_from_line(line, "IF", true)) {
                source.procs[*current].ops.push_back(
                    SourceOp{SourceOp::Kind::If, *expr, {}, i + 1});
            } else if (auto expr = conditional_expr_from_line(line, "ELSEIF", true)) {
                source.procs[*current].ops.push_back(
                    SourceOp{SourceOp::Kind::ElseIf, *expr, {}, i + 1});
            } else if (upper == "ELSE") {
                source.procs[*current].ops.push_back(
                    SourceOp{SourceOp::Kind::Else, {}, {}, i + 1});
            } else if (upper == "FI") {
                source.procs[*current].ops.push_back(
                    SourceOp{SourceOp::Kind::Fi, {}, {}, i + 1});
            } else if (auto clause = for_clause_from_line(line)) {
                source.procs[*current].ops.push_back(
                    SourceOp{SourceOp::Kind::For, cleaned, {}, i + 1});
            } else if (auto expr = conditional_expr_from_line(line, "WHILE", false)) {
                source.procs[*current].ops.push_back(
                    SourceOp{SourceOp::Kind::While, *expr, {}, i + 1});
            } else if (upper == "DO") {
                source.procs[*current].ops.push_back(
                    SourceOp{SourceOp::Kind::Do, {}, {}, i + 1});
            } else if (auto expr = conditional_expr_from_line(line, "UNTIL", false)) {
                source.procs[*current].ops.push_back(
                    SourceOp{SourceOp::Kind::Until, *expr, {}, i + 1});
            } else if (upper == "OD") {
                source.procs[*current].ops.push_back(
                    SourceOp{SourceOp::Kind::Od, {}, {}, i + 1});
            } else if (upper == "EXIT") {
                source.procs[*current].ops.push_back(
                    SourceOp{SourceOp::Kind::Exit, {}, {}, i + 1});
            } else if (auto print_text = print_string_from_line(line)) {
                source.procs[*current].ops.push_back(
                    SourceOp{SourceOp::Kind::Print, *print_text, {}, i + 1});
            } else if (auto expr = print_string_expr_from_line(line)) {
                source.procs[*current].ops.push_back(
                    SourceOp{SourceOp::Kind::PrintString, *expr, {}, i + 1});
            } else if (auto expr = print_int_expr_from_line(line)) {
                source.procs[*current].ops.push_back(
                    SourceOp{SourceOp::Kind::PrintInt, *expr, {}, i + 1});
            } else if (auto expr = print_int_call_from_line(line)) {
                source.procs[*current].ops.push_back(
                    SourceOp{SourceOp::Kind::PrintIntCall, *expr, {}, i + 1});
            } else if (auto real_print = print_real_expr_from_line(line)) {
                source.procs[*current].ops.push_back(SourceOp{
                    SourceOp::Kind::PrintReal,
                    real_print->first,
                    real_print->second ? "NEWLINE" : "",
                    i + 1,
                });
            } else if (auto declaration = reu_declaration_from_line(line)) {
                source.procs[*current].ops.push_back(SourceOp{
                    SourceOp::Kind::ReuDeclare,
                    declaration->name,
                    declaration->size_expression,
                    i + 1,
                });
            } else if (auto declarations = array_declarations_from_line(line);
                       !declarations.empty()) {
                for (const auto& declaration : declarations) {
                    source.procs[*current].ops.push_back(SourceOp{
                        SourceOp::Kind::ArrayDeclare,
                        declaration.name,
                        declaration.type,
                        i + 1,
                        declaration.mode,
                        declaration.expression,
                        declaration.size_expression,
                    });
                }
            } else if (auto declarations = declarations_from_line(line); !declarations.empty()) {
                for (const auto& declaration : declarations) {
                    source.procs[*current].ops.push_back(SourceOp{
                        SourceOp::Kind::Declare,
                        declaration.name,
                        declaration.type,
                        i + 1,
                        declaration.mode,
                        declaration.expression,
                    });
                }
            } else if (auto assignment = assignment_from_line(line)) {
                source.procs[*current].ops.push_back(SourceOp{
                    SourceOp::Kind::Assign,
                    assignment->name,
                    assignment->expression,
                    i + 1,
                    assignment->mode,
                    assignment->index_expression,
                });
            } else if (auto call = call_name_from_line(line)) {
                const std::size_t open = cleaned.find('(');
                const std::size_t close = cleaned.rfind(')');
                const std::string call_args =
                    open == std::string::npos || close == std::string::npos || close <= open
                        ? std::string{}
                        : trim(std::string_view(cleaned).substr(open + 1, close - open - 1));
                source.procs[*current].ops.push_back(
                    SourceOp{SourceOp::Kind::Call, *call, call_args, i + 1});
            } else {
                throw ToolError(
                    "UNSUPPORTED LINE " + std::to_string(i + 1) + ": " + cleaned);
            }
            continue;
        }

        if (upper.rfind("MODULE ", 0) == 0) {
            continue;
        }
        if (auto declaration = reu_declaration_from_line(line)) {
            source.globals.push_back(SourceGlobal{
                declaration->name,
                "REU_BYTE_ARRAY",
                i + 1,
                "STORAGE",
                declaration->size_expression,
                {},
            });
            continue;
        }
        if (auto declarations = array_declarations_from_line(line); !declarations.empty()) {
            for (const auto& declaration : declarations) {
                source.globals.push_back(SourceGlobal{
                    declaration.name,
                    declaration.type + "_ARRAY",
                    i + 1,
                    declaration.mode,
                    declaration.expression,
                    declaration.size_expression,
                });
            }
            continue;
        }
        if (auto declarations = declarations_from_line(line); !declarations.empty()) {
            for (const auto& declaration : declarations) {
                source.globals.push_back(SourceGlobal{
                    declaration.name,
                    declaration.type,
                    i + 1,
                    declaration.mode,
                    declaration.expression,
                    {},
                });
            }
            continue;
        }
        throw ToolError("UNSUPPORTED LINE " + std::to_string(i + 1) + ": " + cleaned);
    }
    if (source.procs.empty()) {
        throw ToolError("NO PROC");
    }
    return source;
}

struct ObjExport {
    std::string name;
    std::uint16_t offset = 0;
    std::uint16_t size = 0;
};

struct ObjReloc {
    std::uint16_t offset = 0;
    bool import = false;
    int import_index = -1;
    std::string symbol;
};

struct ObjBody {
    std::vector<int> imports;
};

struct ObjLineRecord {
    std::uint16_t offset = 0;
    std::size_t line = 0;
};

struct ObjSourceFileRecord {
    std::uint16_t id = 0;
    std::string path;
};

struct ObjProcRecord {
    std::uint16_t export_index = 0;
    std::uint16_t file_id = 0;
    std::size_t line = 0;
    std::size_t column = 0;
};

struct ObjNativeLineRecord {
    std::uint16_t export_index = 0;
    std::uint16_t offset = 0;
    std::uint16_t file_id = 0;
    std::size_t line = 0;
    std::size_t column = 0;
};

struct ObjVariableMetadata {
    std::string name;
    std::uint16_t width = 2;
};

struct ObjVariableRecord {
    char scope = 0;
    char type = 0;
    std::uint16_t export_index = 0;
    std::uint16_t variable_index = 0;
    std::uint16_t file_id = 0;
    std::size_t line = 0;
    std::size_t column = 0;
};

struct ObjectFile {
    std::string module;
    std::string source_file;
    std::vector<ObjSourceFileRecord> source_files;
    std::vector<ObjExport> exports;
    std::vector<ObjBody> bodies;
    std::vector<std::string> imports;
    std::vector<ObjReloc> relocs;
    std::vector<ObjLineRecord> lines;
    std::vector<ObjProcRecord> procedures;
    std::vector<ObjNativeLineRecord> native_lines;
    std::vector<ObjVariableMetadata> variable_metadata;
    std::vector<ObjVariableRecord> variables;
    std::vector<std::uint8_t> code;
};

std::uint16_t parse_object_word(std::string_view text, int base = 0) {
    try {
        std::size_t consumed = 0;
        const unsigned long value = std::stoul(std::string(text), &consumed, base);
        if (consumed != text.size() || value > std::numeric_limits<std::uint16_t>::max()) {
            throw ToolError("BAD OBJECT");
        }
        return static_cast<std::uint16_t>(value);
    } catch (const ToolError&) {
        throw;
    } catch (const std::exception&) {
        throw ToolError("BAD OBJECT");
    }
}

int object_import_index_from_code(char code) {
    if (code >= '0' && code <= '9') {
        return code - '0';
    }
    if (code >= 'A' && code <= 'Z') {
        return code - 'A' + 10;
    }
    if (code >= 'a' && code <= 'z') {
        return code - 'a' + 10;
    }
    throw ToolError("BAD OBJECT");
}

char object_import_code(std::size_t index) {
    if (index < 10) {
        return static_cast<char>('0' + index);
    }
    if (index < 36) {
        return static_cast<char>('A' + index - 10);
    }
    throw ToolError("TOO MANY IMPORTS");
}

std::vector<int> parse_machine_body_marker(std::string_view text) {
    const std::string marker = upper_ascii(trim(text));
    if (marker.empty() || marker.back() != 'M') {
        throw ToolError("UNSUPPORTED OBJECT BODY");
    }

    std::vector<int> imports;
    std::size_t pos = 0;
    while (pos + 1 < marker.size()) {
        if (marker[pos] != 'U') {
            throw ToolError("UNSUPPORTED OBJECT BODY");
        }
        ++pos;
        if (pos + 1 >= marker.size()) {
            throw ToolError("BAD OBJECT");
        }
        imports.push_back(object_import_index_from_code(marker[pos++]));
    }
    if (pos + 1 != marker.size()) {
        throw ToolError("BAD OBJECT");
    }
    return imports;
}

std::size_t parse_object_size(std::string_view text) {
    try {
        std::size_t consumed = 0;
        const unsigned long long value =
            std::stoull(std::string(text), &consumed, 10);
        if (consumed != text.size() ||
            value > std::numeric_limits<std::size_t>::max()) {
            throw ToolError("BAD OBJECT");
        }
        return static_cast<std::size_t>(value);
    } catch (const ToolError&) {
        throw;
    } catch (const std::exception&) {
        throw ToolError("BAD OBJECT");
    }
}

bool is_legacy_placeholder_object(const ObjectFile& object) {
    if (object.code.size() < 2 || object.code.back() != 0) {
        return false;
    }
    const std::string payload(
        object.code.begin(),
        object.code.end() - 1);
    return upper_ascii(payload) == object.module;
}

void validate_object(const ObjectFile& object) {
    if (object.module.empty() || object.exports.empty() || object.code.empty() ||
        object.code.size() > std::numeric_limits<std::uint16_t>::max()) {
        throw ToolError("BAD OBJECT");
    }
    if (is_legacy_placeholder_object(object)) {
        throw ToolError("PLACEHOLDER OBJECT " + object.module);
    }

    std::set<std::string> export_names;
    for (const ObjExport& export_record : object.exports) {
        const std::size_t start = export_record.offset;
        const std::size_t size = export_record.size;
        if (export_record.name.empty() || size == 0 || start >= object.code.size() ||
            size > object.code.size() - start || !export_names.insert(export_record.name).second) {
            throw ToolError("BAD OBJECT");
        }
    }
    for (const ObjReloc& reloc : object.relocs) {
        if (static_cast<std::size_t>(reloc.offset) + 1 >= object.code.size()) {
            throw ToolError("BAD RELOC");
        }
        if (reloc.import) {
            if (reloc.import_index < 0 ||
                static_cast<std::size_t>(reloc.import_index) >= object.imports.size()) {
                throw ToolError("BAD OBJECT");
            }
        } else if (reloc.symbol.empty()) {
            throw ToolError("BAD OBJECT");
        }
    }
    for (const ObjLineRecord& line : object.lines) {
        if (line.line == 0 || line.offset >= object.code.size()) {
            throw ToolError("BAD OBJECT LINE");
        }
    }

    std::set<std::uint16_t> file_ids;
    for (const ObjSourceFileRecord& file : object.source_files) {
        if (file.path.empty() || !file_ids.insert(file.id).second) {
            throw ToolError("BAD OBJECT");
        }
    }
    auto has_file = [&](std::uint16_t id) {
        return file_ids.find(id) != file_ids.end();
    };
    for (const ObjProcRecord& procedure : object.procedures) {
        if (procedure.export_index >= object.exports.size() ||
            !has_file(procedure.file_id) || procedure.line == 0 ||
            procedure.column == 0) {
            throw ToolError("BAD OBJECT");
        }
    }
    for (const ObjNativeLineRecord& line : object.native_lines) {
        if (line.export_index >= object.exports.size() ||
            line.offset >= object.exports[line.export_index].size ||
            !has_file(line.file_id) || line.line == 0 || line.column == 0) {
            throw ToolError("BAD OBJECT LINE");
        }
    }
    for (const ObjVariableMetadata& variable : object.variable_metadata) {
        if (variable.name.empty() || (variable.width != 2 && variable.width != 4)) {
            throw ToolError("BAD OBJECT");
        }
    }
    for (const ObjVariableRecord& variable : object.variables) {
        if ((variable.scope != 'g' && variable.scope != 'p' &&
             variable.scope != 'l') ||
            (variable.type != 'b' && variable.type != 'c' &&
             variable.type != 'i' && variable.type != 'r') ||
            variable.variable_index >= object.variable_metadata.size() ||
            !has_file(variable.file_id) || variable.line == 0 ||
            variable.column == 0 ||
            ((variable.scope == 'p' || variable.scope == 'l') &&
             variable.export_index >= object.exports.size())) {
            throw ToolError("BAD OBJECT");
        }
    }
}

using ExprValue = std::int64_t;

struct VarSlot {
    std::string name;
    std::string lo_symbol;
    std::string hi_symbol;
    bool is_card = false;
    bool is_signed = false;
    std::uint16_t initial_value = 0;
    std::optional<std::uint16_t> absolute_address;

    VarSlot() = default;
    VarSlot(
        std::string variable_name,
        std::string low_symbol,
        std::string high_symbol,
        bool card,
        bool signed_value = false,
        std::uint16_t initial = 0,
        std::optional<std::uint16_t> address = std::nullopt)
        : name(std::move(variable_name)),
          lo_symbol(std::move(low_symbol)),
          hi_symbol(std::move(high_symbol)),
          is_card(card),
          is_signed(signed_value),
          initial_value(initial),
          absolute_address(address) {}
};

enum class IndexedElementType {
    Byte,
    Card,
    Int,
    Real,
};

struct IndexedSlot {
    VarSlot pointer;
    IndexedElementType element_type = IndexedElementType::Byte;

    std::size_t element_width() const {
        if (element_type == IndexedElementType::Real) {
            return 4;
        }
        return element_type == IndexedElementType::Byte ? 1 : 2;
    }

    bool element_is_signed() const {
        return element_type == IndexedElementType::Int;
    }

    bool element_is_real() const {
        return element_type == IndexedElementType::Real;
    }
};

IndexedElementType indexed_element_type(std::string_view type_text) {
    const std::string type = upper_ascii(type_text);
    if (type == "BYTE") return IndexedElementType::Byte;
    if (type == "CARD") return IndexedElementType::Card;
    if (type == "INT") return IndexedElementType::Int;
    if (type == "REAL") return IndexedElementType::Real;
    throw ToolError("BAD INDEXED TYPE " + type);
}

struct ArraySlot {
    IndexedSlot indexed;
    std::string data_symbol;
    std::vector<std::uint8_t> initial_data;
    std::optional<std::uint16_t> absolute_data_address;
};

struct AddressConstantSlot {
    std::string lo_symbol;
    std::string hi_symbol;
    std::string target_symbol;
};

struct RealSlot {
    std::string name;
    std::vector<std::string> byte_symbols;
    std::string pointer_lo_symbol;
    std::string pointer_hi_symbol;
    std::vector<std::uint8_t> initial_value = std::vector<std::uint8_t>(4, 0);
    std::optional<std::uint16_t> absolute_address;
};

struct ExprTempSlot {
    std::string value_lo_symbol;
    std::string value_hi_symbol;
    std::string pointer_lo_symbol;
    std::string pointer_hi_symbol;
};

enum class CallRegister {
    A,
    X,
    Y,
    XY,
    ZeroPage0E,
    ZeroPageE0,
};

struct BuiltinCall {
    std::string helper;
    std::vector<CallRegister> arguments;
    int return_width = 0;
    int carry_low_bit_argument = -1;
};

const std::map<std::string, ExprValue>& builtin_integer_constants() {
    static const std::map<std::string, ExprValue> constants = {
        {"JOY_UP", 0x01},
        {"JOY_DOWN", 0x02},
        {"JOY_LEFT", 0x04},
        {"JOY_RIGHT", 0x08},
        {"JOY_BUTTON1", 0x10},
        {"JOY_BUTTON2", 0x20},
        {"MOUSE_BUTTON1", 0x01},
        {"MOUSE_BUTTON2", 0x02},
        {"SID_TRI", 0x10},
        {"SID_SAW", 0x20},
        {"SID_PULSE", 0x40},
        {"SID_NOISE", 0x80},
        {"SID_LOW", 0x10},
        {"SID_BAND", 0x20},
        {"SID_HIGH", 0x40},
        {"SPR_FRONT", 0},
        {"SPR_BACK", 1},
    };
    return constants;
}

std::optional<BuiltinCall> builtin_call(std::string_view name) {
    static const std::map<std::string, BuiltinCall> calls = {
        {"VICBANK", BuiltinCall{"RT_GFX_VIC_BANK", {CallRegister::A}, 0}},
        {"BGCOLOR", BuiltinCall{"RT_GFX_BGCOLOR", {CallRegister::A}, 0}},
        {"BORDERCOLOR", BuiltinCall{"RT_GFX_BORDERCOLOR", {CallRegister::A}, 0}},
        {"SCREENBASE", BuiltinCall{"RT_GFX_SCREEN_BASE", {CallRegister::XY}, 0}},
        {"BITMAPBASE", BuiltinCall{"RT_GFX_BITMAP_BASE", {CallRegister::XY}, 0}},
        {"SCREENCELL", BuiltinCall{"RT_GFX_SCREEN_CELL", {CallRegister::A, CallRegister::X, CallRegister::Y}, 0}},
        {"COLORCELL", BuiltinCall{"RT_GFX_COLOR_CELL", {CallRegister::A, CallRegister::X, CallRegister::Y}, 0}},
        {"SCREENCOPY", BuiltinCall{"RT_GFX_SCREEN_COPY", {CallRegister::XY}, 0}},
        {"COLORCOPY", BuiltinCall{"RT_GFX_COLOR_COPY", {CallRegister::XY}, 0}},
        {"BITMAPFILL", BuiltinCall{"RT_GFX_BITMAP_FILL", {CallRegister::A}, 0}},
        {"BITMAPCOPY", BuiltinCall{"RT_GFX_BITMAP_COPY", {CallRegister::XY}, 0}},
        {"BITMAPON", BuiltinCall{"RT_GFX_BITMAP_ON", {}, 0}},
        {"BITMAPOFF", BuiltinCall{"RT_GFX_BITMAP_OFF", {}, 0}},
        {"MBITMAPON", BuiltinCall{"RT_GFX_MBITMAP_ON", {}, 0}},
        {"MBITMAPOFF", BuiltinCall{"RT_GFX_MBITMAP_OFF", {}, 0}},
        {"JOY", BuiltinCall{"RT_JOY", {CallRegister::A}, 1}},
        {"JOYSEEN", BuiltinCall{"RT_JP", {CallRegister::A}, 1}},
        {"JOYBTN1", BuiltinCall{"RT_JB1", {CallRegister::A}, 1}},
        {"JOYBTN2", BuiltinCall{"RT_JB2", {CallRegister::A}, 1}},
        {"MOUSEPOLL", BuiltinCall{"RT_MP", {CallRegister::A}, 1}},
        {"MOUSESEEN", BuiltinCall{"RT_MSEEN", {}, 1}},
        {"MOUSEX", BuiltinCall{"RT_MX", {}, 1}},
        {"MOUSEY", BuiltinCall{"RT_MY", {}, 1}},
        {"MOUSEBTN", BuiltinCall{"RT_MB", {}, 1}},
        {"MOUSEBTN1", BuiltinCall{"RT_MB1", {}, 1}},
        {"MOUSEBTN2", BuiltinCall{"RT_MB2", {}, 1}},
        {"SPRITEHIT", BuiltinCall{"RT_SPRITE_HIT", {}, 1}},
        {"SPRITEHITBG", BuiltinCall{"RT_SPRITE_HIT_BG", {}, 1}},
        {"SIDOSC3", BuiltinCall{"RT_SID_OSC3", {}, 1}},
        {"SIDENV3", BuiltinCall{"RT_SID_ENV3", {}, 1}},
        {"SPRITEON", BuiltinCall{"RT_SPRITE_ON", {CallRegister::A}, 0}},
        {"SPRITEOFF", BuiltinCall{"RT_SPRITE_OFF", {CallRegister::A}, 0}},
        {"SPRITEPOS", BuiltinCall{"RT_SPRITE_POS", {CallRegister::A, CallRegister::X, CallRegister::Y}, 0, 1}},
        {"SPRITEPTR", BuiltinCall{"RT_SPRITE_PTR", {CallRegister::X, CallRegister::A}, 0}},
        {"SPRITEDATA", BuiltinCall{"RT_SPRITE_DATA", {CallRegister::A, CallRegister::XY}, 0}},
        {"SPRITECOLOR", BuiltinCall{"RT_SPRITE_COLOR", {CallRegister::X, CallRegister::A}, 0}},
        {"SPRITEMC", BuiltinCall{"RT_SPRITE_MC", {CallRegister::A, CallRegister::Y}, 0}},
        {"SPRITEXEXP", BuiltinCall{"RT_SPRITE_XEXP", {CallRegister::A, CallRegister::Y}, 0}},
        {"SPRITEYEXP", BuiltinCall{"RT_SPRITE_YEXP", {CallRegister::A, CallRegister::Y}, 0}},
        {"SPRITEPRIO", BuiltinCall{"RT_SPRITE_PRIO", {CallRegister::A, CallRegister::Y}, 0}},
        {"SETSPRITEMC", BuiltinCall{"RT_SPRITE_SET_MC", {CallRegister::A, CallRegister::X}, 0}},
        {"SIDFREQ", BuiltinCall{"RT_SID_FREQ", {CallRegister::A, CallRegister::XY}, 0}},
        {"SIDPULSE", BuiltinCall{"RT_SID_PULSE", {CallRegister::A, CallRegister::XY}, 0}},
        {"SIDWAVE", BuiltinCall{"RT_SID_WAVE", {CallRegister::A, CallRegister::Y}, 0}},
        {"SIDAD", BuiltinCall{"RT_SID_AD", {CallRegister::A, CallRegister::Y}, 0}},
        {"SIDSR", BuiltinCall{"RT_SID_SR", {CallRegister::A, CallRegister::Y}, 0}},
        {"SIDON", BuiltinCall{"RT_SID_ON", {CallRegister::A}, 0}},
        {"SIDOFF", BuiltinCall{"RT_SID_OFF", {CallRegister::A}, 0}},
        {"SIDVOL", BuiltinCall{"RT_SID_VOL", {CallRegister::A}, 0}},
        {"SIDCUTOFF", BuiltinCall{"RT_SID_CUTOFF", {CallRegister::XY}, 0}},
        {"SIDRES", BuiltinCall{"RT_SID_RES", {CallRegister::A}, 0}},
        {"SIDMODE", BuiltinCall{"RT_SID_MODE", {CallRegister::A}, 0}},
        {"SIDROUTE", BuiltinCall{"RT_SID_ROUTE", {CallRegister::A}, 0}},
        {"SIDRST", BuiltinCall{"RT_SID_RST", {}, 0}},
        {"REUPEEK8", BuiltinCall{"RT_REU_PEEK8", {CallRegister::A, CallRegister::XY}, 1}},
        {"REUPEEK16", BuiltinCall{"RT_REU_PEEK16", {CallRegister::A, CallRegister::XY}, 2}},
        {"REUPOKE8", BuiltinCall{
            "RT_REU_POKE8",
            {CallRegister::A, CallRegister::XY, CallRegister::ZeroPage0E},
            0,
        }},
        {"REUPOKE16", BuiltinCall{
            "RT_REU_POKE16",
            {CallRegister::A, CallRegister::XY, CallRegister::ZeroPage0E},
            0,
        }},
        {"DBFCREATE", BuiltinCall{"RT_DBF_CREATE", {CallRegister::XY}, 1}},
        {"DBFOPEN", BuiltinCall{"RT_DBF_OPEN", {CallRegister::XY}, 1}},
        {"DBFCLOSE", BuiltinCall{"RT_DBF_CLOSE", {CallRegister::A}, 0}},
        {"DBFGO", BuiltinCall{"RT_DBF_GO", {CallRegister::A, CallRegister::Y}, 1}},
        {"DBFFIELDCOUNT", BuiltinCall{"RT_DBF_FIELDCOUNT", {CallRegister::A}, 1}},
        {"DBFFIELDLEN", BuiltinCall{
            "RT_DBF_FIELDLEN",
            {CallRegister::A, CallRegister::Y},
            1,
        }},
        {"DBFREADBYTE", BuiltinCall{
            "RT_DBF_READBYTE",
            {CallRegister::A, CallRegister::Y},
            1,
        }},
        {"DBFREADFIELDBYTE", BuiltinCall{
            "RT_DBF_READFIELDBYTE",
            {CallRegister::A, CallRegister::X, CallRegister::Y},
            1,
        }},
        {"DBFWRITEFIELDBYTE", BuiltinCall{
            "RT_DBF_WRITEFIELDBYTE",
            {
                CallRegister::A,
                CallRegister::X,
                CallRegister::Y,
                CallRegister::ZeroPageE0,
            },
            1,
        }},
        {"DBFWRITEBYTE", BuiltinCall{
            "RT_DBF_WRITEBYTE",
            {CallRegister::A, CallRegister::X, CallRegister::Y},
            1,
        }},
        {"DBFAPPEND", BuiltinCall{"RT_DBF_APPEND", {CallRegister::A}, 1}},
        {"DBFPACK", BuiltinCall{"RT_DBF_PACK", {CallRegister::A}, 1}},
        {"DBFSAVE", BuiltinCall{"RT_DBF_SAVE", {CallRegister::A}, 1}},
        {"DBFDELETE", BuiltinCall{"RT_DBF_DELETE", {CallRegister::A}, 1}},
        {"DBFUNDELETE", BuiltinCall{"RT_DBF_UNDELETE", {CallRegister::A}, 1}},
        {"DBFDELETED", BuiltinCall{"RT_DBF_DELETED", {CallRegister::A}, 1}},
        {"DBFHEADERLEN", BuiltinCall{"RT_DBF_HEADERLEN", {CallRegister::A}, 1}},
        {"DBFRECORDLEN", BuiltinCall{"RT_DBF_RECORDLEN", {CallRegister::A}, 1}},
        {"DBFTOTALRECS", BuiltinCall{"RT_DBF_TOTALRECS", {CallRegister::A}, 1}},
        {"DBFCURRRECNO", BuiltinCall{"RT_DBF_CURRRECNO", {CallRegister::A}, 1}},
    };
    auto found = calls.find(upper_ascii(name));
    if (found == calls.end()) {
        return std::nullopt;
    }
    return found->second;
}

struct ExprNode {
    enum class Kind {
        Constant,
        StringLiteral,
        Variable,
        Call,
        AddressOf,
        Dereference,
        Negate,
        Add,
        Subtract,
        Multiply,
        Divide,
    };

    Kind kind = Kind::Constant;
    ExprValue value = 0;
    std::string name;
    std::vector<std::string> arguments;
    std::size_t left = 0;
    std::size_t right = 0;
};

struct ParsedExpr {
    std::vector<ExprNode> nodes;
    std::size_t root = 0;
};

class WordExprParser {
public:
    explicit WordExprParser(std::string_view text) : text_(text) {}

    ParsedExpr parse() {
        const std::size_t root = parse_expr();
        skip_ws();
        if (pos_ != text_.size()) {
            throw ToolError("BAD EXPR");
        }
        return ParsedExpr{std::move(nodes_), root};
    }

private:
    void skip_ws() {
        while (pos_ < text_.size() && std::isspace(static_cast<unsigned char>(text_[pos_]))) {
            ++pos_;
        }
    }

    std::size_t add_node(ExprNode node) {
        nodes_.push_back(std::move(node));
        return nodes_.size() - 1;
    }

    std::size_t add_binary(ExprNode::Kind kind, std::size_t left, std::size_t right) {
        ExprNode node;
        node.kind = kind;
        node.left = left;
        node.right = right;
        return add_node(std::move(node));
    }

    std::size_t parse_expr() {
        std::size_t value = parse_term();
        while (true) {
            skip_ws();
            if (pos_ >= text_.size() || (text_[pos_] != '+' && text_[pos_] != '-')) {
                return value;
            }
            const char op = text_[pos_++];
            const std::size_t rhs = parse_term();
            value = add_binary(op == '+' ? ExprNode::Kind::Add : ExprNode::Kind::Subtract, value, rhs);
        }
    }

    std::size_t parse_term() {
        std::size_t value = parse_factor();
        while (true) {
            skip_ws();
            if (pos_ >= text_.size() || (text_[pos_] != '*' && text_[pos_] != '/')) {
                return value;
            }
            const char op = text_[pos_++];
            const std::size_t rhs = parse_factor();
            value = add_binary(op == '*' ? ExprNode::Kind::Multiply : ExprNode::Kind::Divide, value, rhs);
        }
    }

    std::size_t parse_factor() {
        skip_ws();
        if (pos_ >= text_.size()) {
            throw ToolError("BAD EXPR");
        }
        if (text_[pos_] == '(') {
            ++pos_;
            const std::size_t value = parse_expr();
            skip_ws();
            if (pos_ >= text_.size() || text_[pos_] != ')') {
                throw ToolError("BAD EXPR");
            }
            ++pos_;
            return value;
        }
        if (text_[pos_] == '+') {
            ++pos_;
            return parse_factor();
        }
        if (text_[pos_] == '-') {
            ++pos_;
            ExprNode node;
            node.kind = ExprNode::Kind::Negate;
            node.left = parse_factor();
            return add_node(std::move(node));
        }
        if (text_[pos_] == '@') {
            ++pos_;
            ExprNode node;
            node.kind = ExprNode::Kind::AddressOf;
            node.left = parse_factor();
            return add_node(std::move(node));
        }
        if (text_[pos_] == '"') {
            ++pos_;
            ExprNode node;
            node.kind = ExprNode::Kind::StringLiteral;
            bool escaped = false;
            while (pos_ < text_.size()) {
                const char ch = text_[pos_++];
                if (escaped) {
                    if (ch == 'n') {
                        node.name.push_back('\n');
                    } else if (ch == 'r') {
                        node.name.push_back('\r');
                    } else {
                        node.name.push_back(ch);
                    }
                    escaped = false;
                } else if (ch == '\\') {
                    escaped = true;
                } else if (ch == '"') {
                    return add_node(std::move(node));
                } else {
                    node.name.push_back(ch);
                }
            }
            throw ToolError("BAD STRING");
        }

        int base = 10;
        bool explicit_base = false;
        if (text_[pos_] == '$') {
            base = 16;
            explicit_base = true;
            ++pos_;
        } else if (text_[pos_] == '%') {
            base = 2;
            explicit_base = true;
            ++pos_;
        } else if (pos_ + 1 < text_.size() && text_[pos_] == '0' &&
                   (text_[pos_ + 1] == 'x' || text_[pos_ + 1] == 'X')) {
            base = 16;
            explicit_base = true;
            pos_ += 2;
        }
        const std::size_t number_start = pos_;
        ExprValue number = 0;
        while (pos_ < text_.size()) {
            const unsigned char ch = static_cast<unsigned char>(text_[pos_]);
            int digit = -1;
            if (std::isdigit(ch)) {
                digit = ch - '0';
            } else if (std::isalpha(ch)) {
                digit = std::toupper(ch) - 'A' + 10;
            }
            if (digit < 0 || digit >= base) {
                break;
            }
            if (number > (std::numeric_limits<ExprValue>::max() - digit) / base) {
                throw ToolError("EXPR RANGE");
            }
            number = number * base + digit;
            ++pos_;
        }
        if (pos_ != number_start) {
            ExprNode node;
            node.kind = ExprNode::Kind::Constant;
            node.value = number;
            return add_node(std::move(node));
        }
        if (explicit_base || pos_ >= text_.size()) {
            throw ToolError("BAD EXPR");
        }
        if (std::isalpha(static_cast<unsigned char>(text_[pos_])) || text_[pos_] == '_') {
            std::string name;
            while (pos_ < text_.size() &&
                   (std::isalnum(static_cast<unsigned char>(text_[pos_])) || text_[pos_] == '_')) {
                name.push_back(text_[pos_++]);
            }
            ExprNode node;
            node.name = upper_ascii(name);
            skip_ws();
            if (pos_ < text_.size() && text_[pos_] == '(') {
                node.kind = ExprNode::Kind::Call;
                ++pos_;
                skip_ws();
                if (pos_ < text_.size() && text_[pos_] == ')') {
                    ++pos_;
                    return add_node(std::move(node));
                }
                while (pos_ < text_.size()) {
                    const std::size_t start = pos_;
                    int depth = 0;
                    while (pos_ < text_.size()) {
                        const char ch = text_[pos_];
                        if (ch == '(') {
                            ++depth;
                        } else if (ch == ')') {
                            if (depth == 0) {
                                break;
                            }
                            --depth;
                        } else if (ch == ',' && depth == 0) {
                            break;
                        }
                        ++pos_;
                    }
                    std::string argument = trim(text_.substr(start, pos_ - start));
                    if (argument.empty() || pos_ >= text_.size()) {
                        throw ToolError("BAD CALL");
                    }
                    node.arguments.push_back(std::move(argument));
                    if (text_[pos_] == ')') {
                        ++pos_;
                        return add_node(std::move(node));
                    }
                    ++pos_;
                    skip_ws();
                }
                throw ToolError("BAD CALL");
            }
            if (pos_ < text_.size() && text_[pos_] == '^') {
                ++pos_;
                node.kind = ExprNode::Kind::Dereference;
                return add_node(std::move(node));
            }
            node.kind = ExprNode::Kind::Variable;
            return add_node(std::move(node));
        }
        throw ToolError("BAD EXPR");
    }

    std::string_view text_;
    std::vector<ExprNode> nodes_;
    std::size_t pos_ = 0;
};

std::optional<ExprValue> evaluate_expr_node(
    const ParsedExpr& expr,
    std::size_t index,
    const std::map<std::string, ExprValue>& vars) {
    const ExprNode& node = expr.nodes.at(index);
    if (node.kind == ExprNode::Kind::Constant) {
        return node.value;
    }
    if (node.kind == ExprNode::Kind::Variable) {
        auto found = vars.find(node.name);
        if (found == vars.end()) {
            return std::nullopt;
        }
        return found->second;
    }
    if (node.kind == ExprNode::Kind::Call ||
        node.kind == ExprNode::Kind::StringLiteral ||
        node.kind == ExprNode::Kind::AddressOf ||
        node.kind == ExprNode::Kind::Dereference) {
        return std::nullopt;
    }

    const auto lhs = evaluate_expr_node(expr, node.left, vars);
    if (node.kind == ExprNode::Kind::Negate) {
        if (!lhs) {
            return std::nullopt;
        }
        if (*lhs == std::numeric_limits<ExprValue>::min()) {
            throw ToolError("EXPR RANGE");
        }
        return -*lhs;
    }
    const auto rhs = evaluate_expr_node(expr, node.right, vars);
    if (!lhs || !rhs) {
        return std::nullopt;
    }

    if (node.kind == ExprNode::Kind::Add) {
        if ((*rhs > 0 && *lhs > std::numeric_limits<ExprValue>::max() - *rhs) ||
            (*rhs < 0 && *lhs < std::numeric_limits<ExprValue>::min() - *rhs)) {
            throw ToolError("EXPR RANGE");
        }
        return *lhs + *rhs;
    }
    if (node.kind == ExprNode::Kind::Subtract) {
        if ((*rhs < 0 && *lhs > std::numeric_limits<ExprValue>::max() + *rhs) ||
            (*rhs > 0 && *lhs < std::numeric_limits<ExprValue>::min() + *rhs)) {
            throw ToolError("EXPR RANGE");
        }
        return *lhs - *rhs;
    }
    if (node.kind == ExprNode::Kind::Multiply) {
        const __int128 product = static_cast<__int128>(*lhs) * static_cast<__int128>(*rhs);
        if (product > std::numeric_limits<ExprValue>::max() ||
            product < std::numeric_limits<ExprValue>::min()) {
            throw ToolError("EXPR RANGE");
        }
        return static_cast<ExprValue>(product);
    }
    if (*rhs == 0) {
        throw ToolError("DIV ZERO");
    }
    if (*lhs == std::numeric_limits<ExprValue>::min() && *rhs == -1) {
        throw ToolError("EXPR RANGE");
    }
    return *lhs / *rhs;
}

ExprValue eval_const_expr(std::string_view text, const std::map<std::string, ExprValue>& vars) {
    const ParsedExpr expr = WordExprParser(text).parse();
    auto value = evaluate_expr_node(expr, expr.root, vars);
    if (!value) {
        throw ToolError("UNKNOWN VAR");
    }
    return *value;
}

std::optional<ExprValue> try_eval_const_expr(
    std::string_view expr,
    const std::map<std::string, ExprValue>& vars) {
    try {
        return eval_const_expr(expr, vars);
    } catch (const ToolError&) {
        return std::nullopt;
    }
}

struct RealExprNode {
    enum class Kind {
        Constant,
        Variable,
        Call,
        Dereference,
        Negate,
        Add,
        Subtract,
        Multiply,
        Divide,
        Cast,
        Absolute,
        SquareRoot,
    };

    Kind kind = Kind::Constant;
    double value = 0.0;
    std::string name;
    std::vector<std::string> arguments;
    std::size_t left = 0;
    std::size_t right = 0;
};

struct ParsedRealExpr {
    std::vector<RealExprNode> nodes;
    std::size_t root = 0;
};

class RealExprParser {
public:
    explicit RealExprParser(std::string_view text) : text_(text) {}

    ParsedRealExpr parse() {
        const std::size_t root = parse_expr();
        skip_ws();
        if (pos_ != text_.size()) {
            throw ToolError("BAD REAL EXPR");
        }
        return ParsedRealExpr{std::move(nodes_), root};
    }

private:
    void skip_ws() {
        while (pos_ < text_.size() &&
               std::isspace(static_cast<unsigned char>(text_[pos_]))) {
            ++pos_;
        }
    }

    std::size_t add_node(RealExprNode node) {
        nodes_.push_back(std::move(node));
        return nodes_.size() - 1;
    }

    std::size_t add_binary(
        RealExprNode::Kind kind,
        std::size_t left,
        std::size_t right) {
        RealExprNode node;
        node.kind = kind;
        node.left = left;
        node.right = right;
        return add_node(std::move(node));
    }

    std::size_t parse_expr() {
        std::size_t value = parse_term();
        while (true) {
            skip_ws();
            if (pos_ >= text_.size() || (text_[pos_] != '+' && text_[pos_] != '-')) {
                return value;
            }
            const char op = text_[pos_++];
            const std::size_t rhs = parse_term();
            value = add_binary(
                op == '+' ? RealExprNode::Kind::Add : RealExprNode::Kind::Subtract,
                value,
                rhs);
        }
    }

    std::size_t parse_term() {
        std::size_t value = parse_factor();
        while (true) {
            skip_ws();
            if (pos_ >= text_.size() || (text_[pos_] != '*' && text_[pos_] != '/')) {
                return value;
            }
            const char op = text_[pos_++];
            const std::size_t rhs = parse_factor();
            value = add_binary(
                op == '*' ? RealExprNode::Kind::Multiply : RealExprNode::Kind::Divide,
                value,
                rhs);
        }
    }

    std::size_t parse_factor() {
        skip_ws();
        if (pos_ >= text_.size()) {
            throw ToolError("BAD REAL EXPR");
        }
        if (text_[pos_] == '(') {
            ++pos_;
            const std::size_t value = parse_expr();
            skip_ws();
            if (pos_ >= text_.size() || text_[pos_] != ')') {
                throw ToolError("BAD REAL EXPR");
            }
            ++pos_;
            return value;
        }
        if (text_[pos_] == '+') {
            ++pos_;
            return parse_factor();
        }
        if (text_[pos_] == '-') {
            ++pos_;
            RealExprNode node;
            node.kind = RealExprNode::Kind::Negate;
            node.left = parse_factor();
            return add_node(std::move(node));
        }
        if (std::isdigit(static_cast<unsigned char>(text_[pos_])) || text_[pos_] == '.' ||
            text_[pos_] == '$' || text_[pos_] == '%') {
            return parse_number();
        }
        if (std::isalpha(static_cast<unsigned char>(text_[pos_])) || text_[pos_] == '_') {
            return parse_name_or_call();
        }
        throw ToolError("BAD REAL EXPR");
    }

    std::size_t parse_number() {
        const std::size_t start = pos_;
        int base = 10;
        if (text_[pos_] == '$') {
            base = 16;
            ++pos_;
        } else if (text_[pos_] == '%') {
            base = 2;
            ++pos_;
        } else if (pos_ + 1 < text_.size() && text_[pos_] == '0' &&
                   (text_[pos_ + 1] == 'x' || text_[pos_ + 1] == 'X')) {
            base = 16;
            pos_ += 2;
        }
        if (base != 10) {
            const std::size_t digits_start = pos_;
            std::uint64_t value = 0;
            while (pos_ < text_.size()) {
                const unsigned char ch = static_cast<unsigned char>(text_[pos_]);
                int digit = -1;
                if (std::isdigit(ch)) {
                    digit = ch - '0';
                } else if (std::isalpha(ch)) {
                    digit = std::toupper(ch) - 'A' + 10;
                }
                if (digit < 0 || digit >= base) {
                    break;
                }
                if (value > (std::numeric_limits<std::uint64_t>::max() -
                             static_cast<std::uint64_t>(digit)) /
                                static_cast<std::uint64_t>(base)) {
                    throw ToolError("REAL EXPR RANGE");
                }
                value = value * static_cast<std::uint64_t>(base) +
                        static_cast<std::uint64_t>(digit);
                ++pos_;
            }
            if (pos_ == digits_start) {
                throw ToolError("BAD REAL EXPR");
            }
            RealExprNode node;
            node.kind = RealExprNode::Kind::Constant;
            node.value = static_cast<double>(value);
            return add_node(std::move(node));
        }

        const std::string remaining(text_.substr(start));
        char* end = nullptr;
        const double value = std::strtod(remaining.c_str(), &end);
        const std::size_t consumed = static_cast<std::size_t>(end - remaining.c_str());
        if (consumed == 0 || !std::isfinite(value)) {
            throw ToolError("BAD REAL EXPR");
        }
        pos_ = start + consumed;
        RealExprNode node;
        node.kind = RealExprNode::Kind::Constant;
        node.value = value;
        return add_node(std::move(node));
    }

    std::size_t parse_name_or_call() {
        std::string name;
        while (pos_ < text_.size() &&
               (std::isalnum(static_cast<unsigned char>(text_[pos_])) || text_[pos_] == '_')) {
            name.push_back(text_[pos_++]);
        }
        name = upper_ascii(name);
        skip_ws();
        if (pos_ >= text_.size() || text_[pos_] != '(') {
            RealExprNode node;
            if (pos_ < text_.size() && text_[pos_] == '^') {
                ++pos_;
                node.kind = RealExprNode::Kind::Dereference;
            } else {
                node.kind = RealExprNode::Kind::Variable;
            }
            node.name = std::move(name);
            return add_node(std::move(node));
        }

        if (name != "REAL" && name != "FABS" && name != "FSQRT") {
            RealExprNode node;
            node.kind = RealExprNode::Kind::Call;
            node.name = std::move(name);
            ++pos_;
            skip_ws();
            if (pos_ < text_.size() && text_[pos_] == ')') {
                ++pos_;
                return add_node(std::move(node));
            }
            while (pos_ < text_.size()) {
                const std::size_t start = pos_;
                int depth = 0;
                while (pos_ < text_.size()) {
                    const char ch = text_[pos_];
                    if (ch == '(') {
                        ++depth;
                    } else if (ch == ')') {
                        if (depth == 0) {
                            break;
                        }
                        --depth;
                    } else if (ch == ',' && depth == 0) {
                        break;
                    }
                    ++pos_;
                }
                std::string argument = trim(text_.substr(start, pos_ - start));
                if (argument.empty() || pos_ >= text_.size()) {
                    throw ToolError("BAD REAL CALL");
                }
                node.arguments.push_back(std::move(argument));
                if (text_[pos_] == ')') {
                    ++pos_;
                    return add_node(std::move(node));
                }
                ++pos_;
                skip_ws();
            }
            throw ToolError("BAD REAL CALL");
        }

        ++pos_;
        const std::size_t argument = parse_expr();
        skip_ws();
        if (pos_ >= text_.size() || text_[pos_] != ')') {
            throw ToolError("BAD REAL CALL");
        }
        ++pos_;
        RealExprNode node;
        if (name == "REAL") {
            node.kind = RealExprNode::Kind::Cast;
        } else if (name == "FABS") {
            node.kind = RealExprNode::Kind::Absolute;
        } else if (name == "FSQRT") {
            node.kind = RealExprNode::Kind::SquareRoot;
        }
        node.left = argument;
        return add_node(std::move(node));
    }

    std::string_view text_;
    std::size_t pos_ = 0;
    std::vector<RealExprNode> nodes_;
};

std::optional<double> evaluate_real_expr_node(
    const ParsedRealExpr& expr,
    std::size_t index,
    const std::map<std::string, double>& constants) {
    const RealExprNode& node = expr.nodes.at(index);
    if (node.kind == RealExprNode::Kind::Constant) {
        return node.value;
    }
    if (node.kind == RealExprNode::Kind::Variable) {
        auto found = constants.find(node.name);
        if (found == constants.end()) {
            return std::nullopt;
        }
        return found->second;
    }
    if (node.kind == RealExprNode::Kind::Call ||
        node.kind == RealExprNode::Kind::Dereference) {
        return std::nullopt;
    }
    auto lhs = evaluate_real_expr_node(expr, node.left, constants);
    if (!lhs) {
        return std::nullopt;
    }
    if (node.kind == RealExprNode::Kind::Negate) {
        return -*lhs;
    }
    if (node.kind == RealExprNode::Kind::Cast) {
        return *lhs;
    }
    if (node.kind == RealExprNode::Kind::Absolute) {
        return std::fabs(*lhs);
    }
    if (node.kind == RealExprNode::Kind::SquareRoot) {
        if (*lhs < 0.0) {
            throw ToolError("REAL SQRT DOMAIN");
        }
        return std::sqrt(*lhs);
    }
    auto rhs = evaluate_real_expr_node(expr, node.right, constants);
    if (!rhs) {
        return std::nullopt;
    }
    if (node.kind == RealExprNode::Kind::Add) return *lhs + *rhs;
    if (node.kind == RealExprNode::Kind::Subtract) return *lhs - *rhs;
    if (node.kind == RealExprNode::Kind::Multiply) return *lhs * *rhs;
    if (*rhs == 0.0) {
        throw ToolError("REAL DIV ZERO");
    }
    return *lhs / *rhs;
}

std::optional<double> try_eval_const_real_expr(
    std::string_view text,
    const std::map<std::string, double>& constants) {
    try {
        const ParsedRealExpr expr = RealExprParser(text).parse();
        return evaluate_real_expr_node(expr, expr.root, constants);
    } catch (const ToolError&) {
        return std::nullopt;
    }
}

std::vector<std::uint8_t> real32_bytes(double source_value) {
    static_assert(sizeof(float) == sizeof(std::uint32_t));
    static_assert(std::numeric_limits<float>::is_iec559);
    const float value = static_cast<float>(source_value);
    if (!std::isfinite(value)) {
        throw ToolError("REAL RANGE");
    }
    std::uint32_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    return {
        static_cast<std::uint8_t>(bits & 0xFF),
        static_cast<std::uint8_t>((bits >> 8) & 0xFF),
        static_cast<std::uint8_t>((bits >> 16) & 0xFF),
        static_cast<std::uint8_t>((bits >> 24) & 0xFF),
    };
}

struct ParsedComparison {
    std::string lhs;
    std::string op;
    std::string rhs;
};

std::string strip_outer_condition_parentheses(std::string text) {
    text = trim(text);
    while (text.size() >= 2 && text.front() == '(' && text.back() == ')') {
        int depth = 0;
        bool encloses_all = true;
        for (std::size_t i = 0; i < text.size(); ++i) {
            if (text[i] == '(') {
                ++depth;
            } else if (text[i] == ')') {
                --depth;
                if (depth < 0) {
                    throw ToolError("BAD CONDITION");
                }
                if (depth == 0 && i + 1 != text.size()) {
                    encloses_all = false;
                    break;
                }
            }
        }
        if (depth != 0) {
            throw ToolError("BAD CONDITION");
        }
        if (!encloses_all) {
            break;
        }
        text = trim(std::string_view(text).substr(1, text.size() - 2));
    }
    return text;
}

std::optional<ParsedComparison> parse_comparison(std::string_view condition) {
    const std::string text = strip_outer_condition_parentheses(std::string(condition));
    int depth = 0;
    for (std::size_t i = 0; i < text.size(); ++i) {
        if (text[i] == '(') {
            ++depth;
            continue;
        }
        if (text[i] == ')') {
            --depth;
            if (depth < 0) {
                throw ToolError("BAD CONDITION");
            }
            continue;
        }
        if (depth != 0) {
            continue;
        }

        std::string op;
        if (i + 1 < text.size()) {
            const std::string two = text.substr(i, 2);
            if (two == "<=" || two == ">=" || two == "<>" || two == "!=") {
                op = two == "!=" ? "<>" : two;
            }
        }
        if (op.empty() && (text[i] == '=' || text[i] == '<' || text[i] == '>' || text[i] == '#')) {
            op = text[i] == '#' ? "<>" : std::string(1, text[i]);
        }
        if (op.empty()) {
            continue;
        }

        const std::string lhs = trim(std::string_view(text).substr(0, i));
        const std::size_t source_op_size =
            i + 1 < text.size() && (text.substr(i, 2) == "!=" || text.substr(i, 2) == "<=" ||
                                     text.substr(i, 2) == ">=" || text.substr(i, 2) == "<>")
                ? 2
                : 1;
        const std::string rhs = trim(std::string_view(text).substr(i + source_op_size));
        if (lhs.empty() || rhs.empty()) {
            throw ToolError("BAD CONDITION");
        }
        return ParsedComparison{lhs, op, rhs};
    }
    if (depth != 0) {
        throw ToolError("BAD CONDITION");
    }
    return std::nullopt;
}

bool eval_const_condition(
    std::string_view condition,
    const std::map<std::string, ExprValue>& vars) {
    if (auto comparison = parse_comparison(condition)) {
        const ExprValue lhs = eval_const_expr(comparison->lhs, vars);
        const ExprValue rhs = eval_const_expr(comparison->rhs, vars);
        if (comparison->op == "<=") return lhs <= rhs;
        if (comparison->op == ">=") return lhs >= rhs;
        if (comparison->op == "<>") return lhs != rhs;
        if (comparison->op == "=") return lhs == rhs;
        if (comparison->op == "<") return lhs < rhs;
        if (comparison->op == ">") return lhs > rhs;
    }
    return eval_const_expr(strip_outer_condition_parentheses(std::string(condition)), vars) != 0;
}

std::optional<bool> try_eval_const_condition(
    std::string_view condition,
    const std::map<std::string, ExprValue>& vars) {
    try {
        return eval_const_condition(condition, vars);
    } catch (const ToolError&) {
        return std::nullopt;
    }
}

std::string json_string_field(const std::string& text, std::string_view field) {
    const std::string needle = "\"" + std::string(field) + "\"";
    const std::size_t field_pos = text.find(needle);
    if (field_pos == std::string::npos) {
        return {};
    }
    const std::size_t colon = text.find(':', field_pos + needle.size());
    const std::size_t open = text.find('"', colon == std::string::npos ? field_pos : colon);
    if (colon == std::string::npos || open == std::string::npos) {
        return {};
    }
    std::string value;
    for (std::size_t i = open + 1; i < text.size(); ++i) {
        if (text[i] == '"') {
            return value;
        }
        value.push_back(text[i]);
    }
    return {};
}

std::string json_array_body(const std::string& text, std::string_view field) {
    const std::string needle = "\"" + std::string(field) + "\"";
    const std::size_t field_pos = text.find(needle);
    if (field_pos == std::string::npos) {
        return {};
    }
    const std::size_t open = text.find('[', field_pos + needle.size());
    if (open == std::string::npos) {
        return {};
    }
    int depth = 0;
    for (std::size_t i = open; i < text.size(); ++i) {
        if (text[i] == '[') {
            ++depth;
        } else if (text[i] == ']') {
            --depth;
            if (depth == 0) {
                return text.substr(open + 1, i - open - 1);
            }
        }
    }
    return {};
}

std::vector<std::string> json_string_array_field(const std::string& text, std::string_view field) {
    std::vector<std::string> values;
    const std::string body = json_array_body(text, field);
    std::string current;
    bool in_string = false;
    for (char ch : body) {
        if (ch == '"') {
            if (in_string) {
                values.push_back(current);
                current.clear();
            }
            in_string = !in_string;
        } else if (in_string) {
            current.push_back(ch);
        }
    }
    return values;
}

ObjectFile parse_json_object_record(const fs::path& path, const std::string& text) {
    ObjectFile object;
    object.module = upper_ascii(json_string_field(text, "module"));
    if (object.module.empty()) {
        object.module = upper_ascii(path.stem().string());
    }
    const std::string payload_hex = json_string_field(text, "payload_hex");
    if (payload_hex.empty()) {
        throw ToolError("BAD OBJECT");
    }
    object.code = hex_to_bytes(payload_hex);
    if (object.code.size() > std::numeric_limits<std::uint16_t>::max()) {
        throw ToolError("BAD OBJECT");
    }
    for (const std::string& import : json_string_array_field(text, "imports")) {
        object.imports.push_back(upper_ascii(import));
    }

    const std::string exports_body = json_array_body(text, "exports");
    const std::regex export_record("\\[\\s*\"([^\"]+)\"\\s*,\\s*([0-9]+)\\s*\\]");
    for (auto it = std::sregex_iterator(exports_body.begin(), exports_body.end(), export_record);
         it != std::sregex_iterator(); ++it) {
        const std::uint16_t offset = parse_object_word((*it)[2].str(), 10);
        if (offset >= object.code.size()) {
            throw ToolError("BAD OBJECT");
        }
        object.exports.push_back(ObjExport{
            upper_ascii((*it)[1].str()),
            offset,
            static_cast<std::uint16_t>(object.code.size() - offset),
        });
    }
    validate_object(object);
    return object;
}

ObjectFile parse_object_file(const fs::path& path) {
    ObjectFile object;
    object.module = upper_ascii(path.stem().string());
    const auto lines = split_lines(read_text_file(path));
    bool saw_header = false;
    bool saw_body = false;
    for (const std::string& raw : lines) {
        const std::string line = trim(raw);
        if (line.empty()) {
            continue;
        }
        if (!saw_header) {
            if (upper_ascii(line) != "OBJ1") {
                throw ToolError("BAD OBJECT");
            }
            saw_header = true;
            continue;
        }
        if (!line.empty() && line.front() == '{') {
            return parse_json_object_record(path, line);
        }
        const auto words = split_words(line);
        if (words.empty()) {
            continue;
        }
        const std::string record = upper_ascii(words[0]);
        if (record == "X" && words.size() == 4) {
            object.exports.push_back(ObjExport{
                upper_ascii(words[1]),
                parse_object_word(words[2], 10),
                parse_object_word(words[3], 10),
            });
        } else if (record == "B" && words.size() == 2) {
            saw_body = true;
            object.bodies.push_back(ObjBody{
                parse_machine_body_marker(words[1]),
            });
        } else if (record == "U" && words.size() == 2) {
            object.imports.push_back(upper_ascii(words[1]));
        } else if (record == "M" && words.size() >= 2) {
            std::string encoded;
            for (std::size_t i = 1; i < words.size(); ++i) {
                encoded += words[i];
            }
            std::vector<std::uint8_t> chunk = hex_to_bytes(encoded);
            object.code.insert(object.code.end(), chunk.begin(), chunk.end());
        } else if (record == "R" &&
                   (words.size() == 3 || words.size() == 4)) {
            ObjReloc reloc;
            reloc.offset = parse_object_word(words[1], 10);
            const std::string target = upper_ascii(words[2]);
            if (words.size() == 3 && target.size() == 2 && target[0] == 'U') {
                reloc.import = true;
                reloc.import_index = object_import_index_from_code(target[1]);
            } else if (words.size() == 4 && target == "X") {
                reloc.symbol = upper_ascii(words[3]);
            } else {
                throw ToolError("BAD OBJECT");
            }
            object.relocs.push_back(reloc);
        } else if (record == "F" && words.size() >= 2) {
            if (words.size() == 2) {
                if (!object.source_file.empty()) {
                    throw ToolError("BAD OBJECT");
                }
                object.source_file = trim(std::string_view(line).substr(1));
            } else {
                const std::uint16_t file_id = parse_object_word(words[1], 10);
                const std::size_t path_pos = line.find(words[2]);
                if (path_pos == std::string::npos) {
                    throw ToolError("BAD OBJECT");
                }
                object.source_files.push_back(ObjSourceFileRecord{
                    file_id,
                    line.substr(path_pos),
                });
            }
        } else if (words[0] == "l" && words.size() == 3) {
            object.lines.push_back(ObjLineRecord{
                parse_object_word(words[1], 10),
                parse_object_size(words[2]),
            });
        } else if (words[0] == "q" && words.size() == 5) {
            object.procedures.push_back(ObjProcRecord{
                parse_object_word(words[1], 10),
                parse_object_word(words[2], 10),
                parse_object_size(words[3]),
                parse_object_size(words[4]),
            });
        } else if (words[0] == "L" && words.size() == 6) {
            object.native_lines.push_back(ObjNativeLineRecord{
                parse_object_word(words[1], 10),
                parse_object_word(words[2], 10),
                parse_object_word(words[3], 10),
                parse_object_size(words[4]),
                parse_object_size(words[5]),
            });
        } else if (words[0] == "V" &&
                   (words.size() == 7 || words.size() == 8)) {
            if (words[1].size() != 1 || words[2].size() != 1) {
                throw ToolError("BAD OBJECT");
            }
            ObjVariableRecord variable;
            variable.scope = words[1][0];
            variable.type = words[2][0];
            std::size_t pos = 3;
            if (variable.scope == 'p' || variable.scope == 'l') {
                if (words.size() != 8) {
                    throw ToolError("BAD OBJECT");
                }
                variable.export_index = parse_object_word(words[pos++], 10);
            } else if (variable.scope != 'g' || words.size() != 7) {
                throw ToolError("BAD OBJECT");
            }
            variable.variable_index = parse_object_word(words[pos++], 10);
            variable.file_id = parse_object_word(words[pos++], 10);
            variable.line = parse_object_size(words[pos++]);
            variable.column = parse_object_size(words[pos]);
            object.variables.push_back(variable);
        } else if (words[0] == "v" &&
                   (words.size() == 3 || words.size() == 4)) {
            const std::uint16_t width = words.size() == 4
                ? parse_object_word(words[3], 10)
                : 2;
            if (width != 2 && width != 4) {
                throw ToolError("BAD OBJECT");
            }
            parse_object_word(words[2], 10);
            object.variable_metadata.push_back(ObjVariableMetadata{
                words[1],
                width,
            });
        } else if (words[0] == "i" && words.size() == 2) {
            parse_object_word(words[1], 10);
        } else if (words[0] == "k" && words.size() == 2) {
            parse_object_word(words[1], 10);
        } else if (words[0] == "s" && words.size() >= 2) {
            // String metadata is already represented in the native machine bytes.
        } else if (words[0] == "n" && words.size() == 2) {
            // Optional historical display name; exports remain authoritative.
        } else {
            throw ToolError("BAD OBJECT");
        }
    }
    if (!saw_header || !saw_body) {
        throw ToolError("BAD OBJECT");
    }
    if (object.bodies.size() > object.exports.size()) {
        throw ToolError("BAD OBJECT");
    }
    for (const ObjBody& body : object.bodies) {
        for (const int index : body.imports) {
            if (index < 0 ||
                static_cast<std::size_t>(index) >= object.imports.size()) {
                throw ToolError("BAD OBJECT");
            }
        }
    }
    validate_object(object);
    return object;
}

int cmd_actnew(const std::vector<std::string>& args) {
    if (args.empty()) {
        throw ToolError("NO NAME");
    }
    const fs::path root = fs::current_path() / upper_ascii(args.front());
    if (fs::exists(root)) {
        throw ToolError("EXISTS");
    }
    fs::create_directories(root / "SRC");
    fs::create_directories(root / "BIN");
    fs::create_directories(root / "OBJ");
    write_text_file(root / "ACTION.PROJ", "ACTION PROJECT\nMAIN.ACT\n");
    write_text_file(
        root / "README.TXT",
        "UPDATES\nACTION PROJECT READY\n\n"
        "SRC contains Action source.\n"
        "BIN contains build outputs.\n"
        "OBJ contains intermediate artifacts.\n");
    write_text_file(root / "SRC" / "MAIN.ACT", "PROC MAIN()\nENDPROC\n");
    std::cout << "ACTNEW OK\n";
    return 0;
}

int cmd_actadd(const std::vector<std::string>& args) {
    if (args.empty()) {
        throw ToolError("NO NAME");
    }
    const std::string module = module_from_arg(args.front());
    std::vector<std::string> entries = load_manifest_entries(fs::current_path());
    if (manifest_contains_module(entries, module)) {
        throw ToolError("EXISTS");
    }
    const fs::path path = source_path(fs::current_path(), module);
    if (fs::exists(path)) {
        throw ToolError("EXISTS");
    }
    write_text_file(path, "PROC " + module + "()\nENDPROC\n");
    entries.push_back(module + ".ACT");
    save_manifest_entries(fs::current_path(), entries);
    std::cout << "ACTADD OK\n";
    return 0;
}

struct WorkSummary {
    bool project = false;
    bool src = false;
    bool bin = false;
    bool obj = false;
    std::size_t modules = 0;
};

WorkSummary collect_work_summary(const fs::path& root) {
    WorkSummary summary;
    summary.project = child_case_insensitive(root, "ACTION.PROJ").has_value();
    summary.src = child_case_insensitive(root, "SRC").has_value();
    summary.bin = child_case_insensitive(root, "BIN").has_value();
    summary.obj = child_case_insensitive(root, "OBJ").has_value();
    if (summary.project) {
        summary.modules = load_manifest_entries(root).size();
    }
    return summary;
}

void print_work_summary(const WorkSummary& summary) {
    std::cout << "PROJECT " << (summary.project ? "YES" : "NO") << "\n";
    std::cout << "SRC " << (summary.src ? "YES" : "NO") << "\n";
    std::cout << "BIN " << (summary.bin ? "YES" : "NO") << "\n";
    std::cout << "OBJ " << (summary.obj ? "YES" : "NO") << "\n";
    std::cout << "MODULES " << summary.modules << "\n";
}

int cmd_actwork(const std::vector<std::string>&) {
    print_work_summary(collect_work_summary(fs::current_path()));
    return 0;
}

int cmd_actsrc(const std::vector<std::string>&) {
    const auto entries = load_manifest_entries(fs::current_path());
    if (entries.empty()) {
        std::cout << "EMPTY\n";
        return 0;
    }
    for (const std::string& entry : entries) {
        std::cout << entry << "\n";
    }
    return 0;
}

int cmd_actfile(const std::vector<std::string>& args) {
    if (args.empty()) {
        throw ToolError("NO NAME");
    }
    const std::string module = module_from_arg(args.front());
    require_project_module(fs::current_path(), module);
    const fs::path path = source_path(fs::current_path(), module);
    if (!fs::is_regular_file(path)) {
        throw ToolError("NO FILE");
    }
    std::cout << read_text_file(path);
    return 0;
}

int cmd_actchk(const std::vector<std::string>&) {
    const auto entries = load_manifest_entries(fs::current_path());
    WorkSummary summary = collect_work_summary(fs::current_path());
    print_work_summary(summary);

    std::vector<std::string> missing;
    for (const std::string& entry : entries) {
        std::string module = entry;
        const std::string suffix = ".ACT";
        if (module.size() >= suffix.size() &&
            upper_ascii(std::string_view(module).substr(module.size() - suffix.size())) == suffix) {
            module.resize(module.size() - suffix.size());
        }
        if (!fs::is_regular_file(source_path(fs::current_path(), module))) {
            missing.push_back(entry);
        }
    }
    std::cout << "MISSING " << missing.size() << "\n";
    for (const std::string& entry : missing) {
        std::cout << "MISSING " << entry << "\n";
    }
    if (!summary.src || !summary.bin || !summary.obj || !missing.empty()) {
        std::cout << "ACTCHK BROKEN\n";
        return 1;
    }
    std::cout << "ACTCHK OK\n";
    return 0;
}

int cmd_actdir(const std::vector<std::string>& args) {
    const fs::path dir = args.empty() ? fs::current_path() : fs::path(args.front());
    if (!fs::is_directory(dir)) {
        throw ToolError("NO DIR");
    }
    std::vector<std::string> entries;
    for (const auto& entry : fs::directory_iterator(dir)) {
        const std::string prefix = entry.is_directory() ? "D " : "F ";
        entries.push_back(prefix + entry.path().filename().string());
    }
    std::sort(entries.begin(), entries.end(), [](const std::string& a, const std::string& b) {
        return upper_ascii(a) < upper_ascii(b);
    });
    for (const std::string& entry : entries) {
        std::cout << entry << "\n";
    }
    return 0;
}

int cmd_actcopy(const std::vector<std::string>& args) {
    if (args.size() < 2) {
        throw ToolError("BAD COPY");
    }
    const fs::path src = args[0];
    const fs::path dst = args[1];
    if (!fs::is_regular_file(src)) {
        throw ToolError("NO SUCH FILE");
    }
    fs::create_directories(dst.parent_path().empty() ? fs::path(".") : dst.parent_path());
    fs::copy_file(src, dst, fs::copy_options::overwrite_existing);
    std::cout << "ACTCOPY OK\n";
    return 0;
}

int cmd_actdel(const std::vector<std::string>& args) {
    if (args.empty()) {
        throw ToolError("NO NAME");
    }
    const fs::path target = args.front();
    if (!fs::is_regular_file(target)) {
        throw ToolError("NO SUCH FILE");
    }
    fs::remove(target);
    std::cout << "ACTDEL OK\n";
    return 0;
}

int cmd_actmkdir(const std::vector<std::string>& args) {
    if (args.empty()) {
        throw ToolError("NO NAME");
    }
    fs::create_directories(args.front());
    std::cout << "ACTMKDIR OK\n";
    return 0;
}

int cmd_actrmdir(const std::vector<std::string>& args) {
    if (args.empty()) {
        throw ToolError("NO NAME");
    }
    const fs::path target = args.front();
    if (!fs::is_directory(target)) {
        throw ToolError("NO DIR");
    }
    if (!fs::remove(target)) {
        throw ToolError("RMDIR FAIL");
    }
    std::cout << "ACTRMDIR OK\n";
    return 0;
}

int cmd_actmove(const std::vector<std::string>& args) {
    if (args.size() < 2) {
        throw ToolError("BAD MOVE");
    }
    const fs::path src = args[0];
    const fs::path dst = args[1];
    if (!fs::exists(src)) {
        throw ToolError("NO SUCH FILE");
    }
    fs::create_directories(dst.parent_path().empty() ? fs::path(".") : dst.parent_path());
    fs::rename(src, dst);
    std::cout << "ACTMOVE OK\n";
    return 0;
}

int cmd_actwrite(const std::vector<std::string>& args) {
    if (args.empty()) {
        throw ToolError("NO NAME");
    }
    std::string text;
    for (std::size_t i = 1; i < args.size(); ++i) {
        if (i > 1) {
            text += " ";
        }
        text += args[i];
    }
    if (!text.empty()) {
        text += "\n";
    }
    write_text_file(args.front(), text);
    std::cout << "ACTWRITE OK\n";
    return 0;
}

int cmd_actinfo(const std::vector<std::string>&) {
    std::cout << "ACTIONC64U IDUN LINUX TOOLS\n";
    std::cout << "TOOLS C++17\n";
    std::cout << "OUTPUT C64 PRG\n";
    return 0;
}

fs::path action_state_path(const fs::path& root, std::string_view filename) {
    return root / ".action" / std::string(filename);
}

void rebuild_source_index(const fs::path& root) {
    SqliteDatabase database(action_state_path(root, "workspace.sqlite3"));
    database.exec(
        "CREATE TABLE IF NOT EXISTS source_lines("
        "module TEXT NOT NULL,path TEXT NOT NULL,line INTEGER NOT NULL,"
        "text TEXT NOT NULL,PRIMARY KEY(module,line))");
    database.exec(
        "CREATE TABLE IF NOT EXISTS source_symbols("
        "name TEXT NOT NULL,kind TEXT NOT NULL,module TEXT NOT NULL,"
        "path TEXT NOT NULL,line INTEGER NOT NULL)");
    database.exec(
        "CREATE INDEX IF NOT EXISTS source_symbols_name "
        "ON source_symbols(name COLLATE NOCASE)");
    database.exec("BEGIN IMMEDIATE");
    try {
        database.exec("DELETE FROM source_lines");
        database.exec("DELETE FROM source_symbols");
        SqliteStatement insert_line(
            database,
            "INSERT INTO source_lines(module,path,line,text) VALUES(?,?,?,?)");
        SqliteStatement insert_symbol(
            database,
            "INSERT INTO source_symbols(name,kind,module,path,line) "
            "VALUES(?,?,?,?,?)");
        const std::regex structural_symbol(
            R"(^\s*(MODULE|PROC|OVERLAY|BYTE\s+FUNC|CARD\s+FUNC|INT\s+FUNC|REAL\s+FUNC)\s+([A-Za-z_][A-Za-z0-9_]*))",
            std::regex_constants::icase);
        const std::regex data_symbol(
            R"(^\s*(BYTE|CARD|INT|REAL)\s+(?:ARRAY\s+|POINTER\s+)?([A-Za-z_][A-Za-z0-9_]*))",
            std::regex_constants::icase);

        for (const std::string& entry : load_manifest_entries(root)) {
            const std::string module = module_from_arg(entry);
            const fs::path source = source_path(root, module);
            if (!fs::is_regular_file(source)) {
                continue;
            }
            const std::string relative = fs::relative(source, root).generic_string();
            const std::vector<std::string> lines =
                split_lines(read_text_file(source));
            for (std::size_t i = 0; i < lines.size(); ++i) {
                insert_line.bind_text(1, module);
                insert_line.bind_text(2, relative);
                insert_line.bind_integer(3, static_cast<std::int64_t>(i + 1));
                insert_line.bind_text(4, lines[i]);
                insert_line.step();
                insert_line.reset();

                const std::string code = strip_source_comment(lines[i]);
                std::smatch match;
                std::string kind;
                std::string name;
                if (std::regex_search(code, match, structural_symbol)) {
                    kind = upper_ascii(match[1].str());
                    name = upper_ascii(match[2].str());
                } else if (std::regex_search(code, match, data_symbol)) {
                    kind = upper_ascii(match[1].str());
                    name = upper_ascii(match[2].str());
                }
                if (!name.empty()) {
                    insert_symbol.bind_text(1, name);
                    insert_symbol.bind_text(2, kind);
                    insert_symbol.bind_text(3, module);
                    insert_symbol.bind_text(4, relative);
                    insert_symbol.bind_integer(
                        5, static_cast<std::int64_t>(i + 1));
                    insert_symbol.step();
                    insert_symbol.reset();
                }
            }
        }
        database.exec("COMMIT");
    } catch (...) {
        try {
            database.exec("ROLLBACK");
        } catch (...) {
        }
        throw;
    }
}

void print_source_matches(const fs::path& root, std::string_view query) {
    rebuild_source_index(root);
    SqliteDatabase database(action_state_path(root, "workspace.sqlite3"));
    SqliteStatement select(
        database,
        "SELECT path,line,text FROM source_lines "
        "WHERE instr(lower(text),lower(?))>0 ORDER BY path,line");
    select.bind_text(1, query);
    while (select.step()) {
        std::cout << select.text(0) << ":" << select.integer(1) << ":"
                  << select.text(2) << "\n";
    }
}

void print_source_symbols(const fs::path& root, std::string_view module) {
    rebuild_source_index(root);
    SqliteDatabase database(action_state_path(root, "workspace.sqlite3"));
    SqliteStatement select(
        database,
        "SELECT kind,name,path,line FROM source_symbols "
        "WHERE module=? ORDER BY line,name");
    select.bind_text(1, upper_ascii(module));
    while (select.step()) {
        std::cout << select.text(0) << " " << select.text(1) << " "
                  << select.text(2) << ":" << select.integer(3) << "\n";
    }
}

int cmd_actmon(const std::vector<std::string>&) {
    const fs::path root = fs::current_path();
    std::cout << "ACTIONC64U MONITOR\n";
    print_work_summary(collect_work_summary(root));
    if (child_case_insensitive(root, "ACTION.PROJ").has_value()) {
        const auto entries = load_manifest_entries(root);
        std::cout << "SOURCES\n";
        for (const std::string& entry : entries) {
            std::cout << "  " << entry << "\n";
        }
    }
    std::cout << "COMMANDS actnew actadd actedit actc alink actdbg actchk\n";
    return 0;
}

struct DebugLineInfo {
    std::uint16_t address = 0;
    int module_id = 0;
    int file_id = 0;
    std::size_t line = 0;
};

struct DebugSymbolInfo {
    std::uint16_t address = 0;
    std::uint16_t size = 0;
    std::string name;
};

struct DebugSidecar {
    std::map<int, std::string> modules;
    std::map<std::pair<int, int>, std::string> source_files;
    std::vector<DebugLineInfo> lines;
    std::vector<DebugSymbolInfo> symbols;
};

DebugSidecar parse_debug_sidecar(const fs::path& path) {
    DebugSidecar sidecar;
    for (const std::string& raw : split_lines(read_text_file(path))) {
        const std::string line = trim(raw);
        const std::vector<std::string> words = split_words(line);
        if (words.empty()) {
            continue;
        }
        if (words[0] == "m" && words.size() >= 3) {
            sidecar.modules[static_cast<int>(parse_object_size(words[1]))] =
                words[2];
        } else if (words[0] == "f" && words.size() >= 3) {
            const int module_id =
                static_cast<int>(parse_object_size(words[1]));
            const bool canonical =
                words.size() >= 4 &&
                std::all_of(words[2].begin(), words[2].end(), [](char ch) {
                    return std::isdigit(static_cast<unsigned char>(ch));
                });
            const int file_id = canonical
                ? static_cast<int>(parse_object_size(words[2]))
                : 0;
            const std::size_t path_word = canonical ? 3 : 2;
            const std::size_t path_pos = line.find(words[path_word]);
            sidecar.source_files[{module_id, file_id}] =
                path_pos == std::string::npos
                    ? words[path_word]
                    : line.substr(path_pos);
        } else if (words[0] == "l" && words.size() >= 4) {
            if (words.size() >= 7) {
                sidecar.lines.push_back(DebugLineInfo{
                    parse_object_word(words[3], 10),
                    static_cast<int>(parse_object_size(words[1])),
                    static_cast<int>(parse_object_size(words[4])),
                    parse_object_size(words[5]),
                });
            } else {
                sidecar.lines.push_back(DebugLineInfo{
                    parse_object_word(words[1], 10),
                    static_cast<int>(parse_object_size(words[2])),
                    0,
                    parse_object_size(words[3]),
                });
            }
        } else if (words[0] == "y" && words.size() >= 4) {
            sidecar.symbols.push_back(DebugSymbolInfo{
                parse_object_word(words[1]),
                parse_object_word(words[2]),
                upper_ascii(words[3]),
            });
        }
    }
    return sidecar;
}

std::uint16_t parse_debug_address(std::string_view text) {
    std::string value = trim(text);
    int base = 10;
    if (!value.empty() && value.front() == '$') {
        value.erase(value.begin());
        base = 16;
    } else if (value.size() > 2 && value[0] == '0' &&
               (value[1] == 'x' || value[1] == 'X')) {
        value.erase(0, 2);
        base = 16;
    }
    return parse_object_word(value, base);
}

std::optional<DebugLineInfo> debug_line_for_source(
    const DebugSidecar& sidecar,
    int module_id,
    std::size_t line) {
    std::optional<DebugLineInfo> best;
    for (const DebugLineInfo& candidate : sidecar.lines) {
        if (candidate.module_id == module_id && candidate.line == line &&
            (!best || candidate.address < best->address)) {
            best = candidate;
        }
    }
    return best;
}

std::optional<DebugLineInfo> debug_line_for_address(
    const DebugSidecar& sidecar,
    std::uint16_t address) {
    std::optional<DebugLineInfo> best;
    for (const DebugLineInfo& candidate : sidecar.lines) {
        if (candidate.address <= address &&
            (!best || candidate.address > best->address)) {
            best = candidate;
        }
    }
    return best;
}

std::string debug_source_name(
    const DebugSidecar& sidecar,
    int module_id,
    int file_id) {
    auto source = sidecar.source_files.find({module_id, file_id});
    if (source != sidecar.source_files.end()) {
        return source->second;
    }
    auto module = sidecar.modules.find(module_id);
    return module == sidecar.modules.end()
        ? std::string{"UNKNOWN"}
        : "SRC/" + module->second + ".ACT";
}

void ensure_breakpoint_schema(SqliteDatabase& database) {
    database.exec(
        "CREATE TABLE IF NOT EXISTS breakpoints("
        "id INTEGER PRIMARY KEY,module TEXT NOT NULL,source TEXT NOT NULL,"
        "line INTEGER NOT NULL,address INTEGER NOT NULL,enabled INTEGER NOT NULL "
        "DEFAULT 1,UNIQUE(module,source,line))");
}

void store_breakpoint(
    const fs::path& root,
    std::string_view module,
    const std::string& source,
    const DebugLineInfo& location) {
    SqliteDatabase database(action_state_path(root, "debug.sqlite3"));
    ensure_breakpoint_schema(database);
    SqliteStatement upsert(
        database,
        "INSERT INTO breakpoints(module,source,line,address,enabled) "
        "VALUES(?,?,?,?,1) ON CONFLICT(module,source,line) DO UPDATE SET "
        "address=excluded.address,enabled=1");
    upsert.bind_text(1, upper_ascii(module));
    upsert.bind_text(2, source);
    upsert.bind_integer(3, static_cast<std::int64_t>(location.line));
    upsert.bind_integer(4, location.address);
    upsert.step();

    SqliteStatement select(
        database,
        "SELECT id FROM breakpoints WHERE module=? AND source=? AND line=?");
    select.bind_text(1, upper_ascii(module));
    select.bind_text(2, source);
    select.bind_integer(3, static_cast<std::int64_t>(location.line));
    if (!select.step()) {
        throw ToolError("BREAKPOINT STORE FAIL");
    }
    std::cout << "BREAKPOINT " << select.integer(0) << " "
              << location.address << " " << source << ":" << location.line
              << "\n";
}

void list_breakpoints(const fs::path& root, std::string_view module) {
    SqliteDatabase database(action_state_path(root, "debug.sqlite3"));
    ensure_breakpoint_schema(database);
    SqliteStatement select(
        database,
        "SELECT id,address,source,line,enabled FROM breakpoints "
        "WHERE module=? ORDER BY source,line");
    select.bind_text(1, upper_ascii(module));
    while (select.step()) {
        std::cout << "BREAKPOINT " << select.integer(0) << " "
                  << select.integer(1) << " " << select.text(2) << ":"
                  << select.integer(3) << " "
                  << (select.integer(4) != 0 ? "ENABLED" : "DISABLED")
                  << "\n";
    }
}

void clear_breakpoint(
    const fs::path& root,
    std::string_view module,
    std::size_t id) {
    SqliteDatabase database(action_state_path(root, "debug.sqlite3"));
    ensure_breakpoint_schema(database);
    SqliteStatement remove(
        database,
        "DELETE FROM breakpoints WHERE module=? AND id=?");
    remove.bind_text(1, upper_ascii(module));
    remove.bind_integer(2, static_cast<std::int64_t>(id));
    remove.step();
    if (sqlite3_changes(database.get()) == 0) {
        throw ToolError("NO BREAKPOINT");
    }
    std::cout << "BREAKPOINT CLEARED " << id << "\n";
}

int cmd_actdbg(const std::vector<std::string>& args) {
    if (args.empty()) {
        throw ToolError("NO NAME");
    }
    const std::string module = module_from_arg(args.front());
    const fs::path prg = binary_path(fs::current_path(), module);
    const fs::path dbg = debug_path(fs::current_path(), module);
    if (!fs::is_regular_file(prg)) {
        throw ToolError("NO PRG");
    }
    if (!fs::is_regular_file(dbg)) {
        throw ToolError("NO DBG");
    }
    std::ifstream in(prg, std::ios::binary | std::ios::ate);
    if (!in) {
        throw ToolError("LOAD FAIL");
    }
    const std::streamoff size = in.tellg();
    if (size < 3) {
        throw ToolError("BAD PRG");
    }
    in.seekg(0);
    const int lo = in.get();
    const int hi = in.get();
    const std::uint16_t load_address = static_cast<std::uint16_t>(lo | (hi << 8));
    const DebugSidecar sidecar = parse_debug_sidecar(dbg);

    if (args.size() >= 2) {
        const std::string mode = upper_ascii(args[1]);
        if (mode == "--SYMBOLS" || mode == "SYMBOLS") {
            const std::string filter =
                args.size() >= 3 ? upper_ascii(args[2]) : std::string{};
            for (const DebugSymbolInfo& symbol : sidecar.symbols) {
                if (filter.empty() || symbol.name.find(filter) != std::string::npos) {
                    std::cout << "SYMBOL " << symbol.address << " "
                              << symbol.size << " " << symbol.name << "\n";
                }
            }
            return 0;
        }
        if ((mode == "--SOURCE" || mode == "SOURCE") && args.size() >= 3) {
            const std::uint16_t address = parse_debug_address(args[2]);
            auto location = debug_line_for_address(sidecar, address);
            if (!location) {
                throw ToolError("NO SOURCE LOCATION");
            }
            std::cout << "SOURCE " << location->address << " "
                      << debug_source_name(
                             sidecar, location->module_id, location->file_id)
                      << ":" << location->line << "\n";
            return 0;
        }
        if ((mode == "--LINE" || mode == "LINE") && args.size() >= 3) {
            const std::size_t line = parse_object_size(args[2]);
            auto location = debug_line_for_source(sidecar, 0, line);
            if (!location) {
                throw ToolError("NO SOURCE LINE");
            }
            std::cout << "ADDRESS " << location->address << " "
                      << debug_source_name(
                             sidecar, location->module_id, location->file_id)
                      << ":" << location->line << "\n";
            return 0;
        }
        if ((mode == "--BREAK" || mode == "BREAK") && args.size() >= 3) {
            const std::size_t line = parse_object_size(args[2]);
            auto location = debug_line_for_source(sidecar, 0, line);
            if (!location) {
                throw ToolError("NO SOURCE LINE");
            }
            store_breakpoint(
                fs::current_path(),
                module,
                debug_source_name(
                    sidecar, location->module_id, location->file_id),
                *location);
            return 0;
        }
        if (mode == "--BREAKS" || mode == "BREAKS") {
            list_breakpoints(fs::current_path(), module);
            return 0;
        }
        if ((mode == "--CLEAR" || mode == "CLEAR") && args.size() >= 3) {
            clear_breakpoint(
                fs::current_path(),
                module,
                parse_object_size(args[2]));
            return 0;
        }
        throw ToolError("BAD DEBUG COMMAND");
    }

    std::cout << "ACTDBG INFO\n";
    std::cout << "MODULE " << module << "\n";
    std::cout << "PRG " << prg.generic_string() << "\n";
    std::cout << "LOAD " << load_address << "\n";
    std::cout << "SIZE " << (size - 2) << "\n";

    const auto lines = split_lines(read_text_file(dbg));
    for (const std::string& raw : lines) {
        const std::string line = trim(raw);
        if (line.empty() || upper_ascii(line) == "DBG1") {
            continue;
        }
        std::cout << line << "\n";
    }
    return 0;
}

void collect_tree_entries(const fs::path& root, const fs::path& current, std::vector<std::string>& entries) {
    std::vector<fs::directory_entry> children;
    for (const auto& entry : fs::directory_iterator(current)) {
        children.push_back(entry);
    }
    std::sort(children.begin(), children.end(), [](const auto& a, const auto& b) {
        return upper_ascii(a.path().filename().string()) < upper_ascii(b.path().filename().string());
    });
    for (const auto& entry : children) {
        const fs::path relative = fs::relative(entry.path(), root);
        entries.push_back(std::string(entry.is_directory() ? "D " : "F ") + relative.generic_string());
        if (entry.is_directory()) {
            collect_tree_entries(root, entry.path(), entries);
        }
    }
}

int cmd_acttree(const std::vector<std::string>& args) {
    const fs::path root = args.empty() ? fs::current_path() : fs::path(args.front());
    if (!fs::is_directory(root)) {
        throw ToolError("NO DIR");
    }
    std::vector<std::string> entries;
    collect_tree_entries(root, root, entries);
    for (const std::string& entry : entries) {
        std::cout << entry << "\n";
    }
    return 0;
}

int cmd_xcopy(const std::vector<std::string>& args) {
    if (args.size() < 2) {
        throw ToolError("BAD COPY");
    }
    if (!fs::exists(args[0])) {
        throw ToolError("NO SUCH FILE");
    }
    fs::copy(args[0], args[1], fs::copy_options::recursive | fs::copy_options::overwrite_existing);
    std::cout << "XCOPY OK\n";
    return 0;
}

int cmd_deltree(const std::vector<std::string>& args) {
    if (args.empty()) {
        throw ToolError("NO NAME");
    }
    if (!fs::exists(args.front())) {
        throw ToolError("NO SUCH FILE");
    }
    fs::remove_all(args.front());
    std::cout << "DELTREE OK\n";
    return 0;
}

int cmd_actedit(const std::vector<std::string>& args) {
    if (args.empty()) {
        throw ToolError("NO NAME");
    }
    const std::string module = module_from_arg(args.front());
    require_project_module(fs::current_path(), module);
    const fs::path path = source_path(fs::current_path(), module);
    std::vector<std::string> lines = read_source_lines(path);

    if (args.size() == 1) {
        const char* editor = std::getenv("EDITOR");
        if (editor != nullptr && *editor != '\0') {
            const std::string command = std::string(editor) + " " + shell_quote(path);
            const int status = std::system(command.c_str());
            if (status != 0) {
                throw ToolError("EDIT FAIL");
            }
            std::cout << "ACTEDIT OK\n";
            return 0;
        }
        std::cout << read_text_file(path);
        return 0;
    }

    const std::string mode = upper_ascii(args[1]);
    if (mode == "--INDEX" || mode == "INDEX") {
        rebuild_source_index(fs::current_path());
        std::cout << "ACTEDIT INDEXED\n";
        return 0;
    }
    if ((mode == "--FIND" || mode == "FIND") && args.size() >= 3) {
        std::string query;
        for (std::size_t i = 2; i < args.size(); ++i) {
            if (!query.empty()) {
                query.push_back(' ');
            }
            query += args[i];
        }
        print_source_matches(fs::current_path(), query);
        return 0;
    }
    if (mode == "--SYMBOLS" || mode == "SYMBOLS") {
        print_source_symbols(fs::current_path(), module);
        return 0;
    }
    if (mode == "--PRINT" || mode == "PRINT") {
        std::cout << read_text_file(path);
        return 0;
    }
    if ((mode == "--APPEND" || mode == "APPEND") && args.size() >= 3) {
        lines.push_back(args[2]);
        write_text_file(path, join_lines(lines));
        std::cout << "ACTEDIT OK\n";
        return 0;
    }
    if ((mode == "--INSERT" || mode == "INSERT") && args.size() >= 4) {
        const std::size_t index = parse_one_based_line(args[2], lines.size() + 1);
        lines.insert(lines.begin() + static_cast<std::ptrdiff_t>(index), args[3]);
        write_text_file(path, join_lines(lines));
        std::cout << "ACTEDIT OK\n";
        return 0;
    }
    if ((mode == "--REPLACE" || mode == "REPLACE") && args.size() >= 4) {
        const std::size_t index = parse_one_based_line(args[2], lines.size());
        lines[index] = args[3];
        write_text_file(path, join_lines(lines));
        std::cout << "ACTEDIT OK\n";
        return 0;
    }
    if ((mode == "--DELETE" || mode == "DELETE") && args.size() >= 3) {
        const std::size_t index = parse_one_based_line(args[2], lines.size());
        lines.erase(lines.begin() + static_cast<std::ptrdiff_t>(index));
        write_text_file(path, join_lines(lines));
        std::cout << "ACTEDIT OK\n";
        return 0;
    }
    throw ToolError("BAD EDIT");
}

int cmd_alink(const std::vector<std::string>& args);

int cmd_act2save(const std::vector<std::string>& args) {
    const std::vector<std::string> link_args = args.empty() ? std::vector<std::string>{"MAIN"} : args;
    int status = cmd_alink(link_args);
    if (status == 0) {
        std::cout << "ACT2SAVE OK\n";
    }
    return status;
}

int cmd_actc(const std::vector<std::string>& args) {
    if (args.empty()) {
        throw ToolError("NO NAME");
    }
    const std::string module = module_from_arg(args.front());
    require_project_module(fs::current_path(), module);
    const fs::path src = source_path(fs::current_path(), module);
    if (!fs::is_regular_file(src)) {
        throw ToolError("NO FILE");
    }

    ParsedSource source = parse_source(read_text_file(src));
    std::vector<SourceProc>& procs = source.procs;
    auto main_it = std::find_if(procs.begin(), procs.end(), [](const SourceProc& proc) {
        return upper_ascii(proc.name) == "MAIN";
    });
    if (main_it == procs.end()) {
        throw ToolError("NO MAIN");
    }
    if (!main_it->return_type.empty()) {
        throw ToolError("MAIN MUST BE PROC LINE " + std::to_string(main_it->line));
    }

    std::vector<SourceProc> ordered;
    ordered.push_back(*main_it);
    for (const SourceProc& proc : procs) {
        if (upper_ascii(proc.name) != "MAIN") {
            ordered.push_back(proc);
        }
    }

    std::set<std::string> local_names;
    std::set<std::string> overlay_names;
    for (const SourceProc& proc : ordered) {
        const std::string name = upper_ascii(proc.name);
        if (!local_names.insert(name).second) {
            throw ToolError(
                "DUPLICATE PROC LINE " + std::to_string(proc.line) + ": " + name);
        }
        if (proc.is_overlay) {
            overlay_names.insert(name);
        }
    }

    std::map<std::string, std::set<std::string>> local_call_graph;
    auto collect_local_call_targets = [&](
        std::string_view text,
        std::set<std::string>& targets) {
        bool in_string = false;
        for (std::size_t i = 0; i < text.size();) {
            const char ch = text[i];
            if (in_string && ch == '\\' && i + 1 < text.size()) {
                i += 2;
                continue;
            }
            if (ch == '"') {
                in_string = !in_string;
                ++i;
                continue;
            }
            if (in_string ||
                (!std::isalnum(static_cast<unsigned char>(ch)) && ch != '_')) {
                ++i;
                continue;
            }
            const std::size_t start = i;
            while (i < text.size() &&
                   (std::isalnum(static_cast<unsigned char>(text[i])) || text[i] == '_')) {
                ++i;
            }
            std::size_t next = i;
            while (next < text.size() &&
                   std::isspace(static_cast<unsigned char>(text[next]))) {
                ++next;
            }
            const std::string name = upper_ascii(text.substr(start, i - start));
            if (next < text.size() && text[next] == '(' &&
                local_names.count(name) != 0) {
                targets.insert(name);
            }
        }
    };
    for (const SourceProc& proc : ordered) {
        const std::string caller = upper_ascii(proc.name);
        std::set<std::string>& targets = local_call_graph[caller];
        for (const SourceOp& op : proc.ops) {
            if (op.kind == SourceOp::Kind::Call) {
                const std::string target = upper_ascii(op.value);
                if (local_names.count(target) != 0) {
                    targets.insert(target);
                }
            }
            if (op.kind == SourceOp::Kind::Print) {
                continue;
            }
            collect_local_call_targets(op.value, targets);
            collect_local_call_targets(op.aux, targets);
            collect_local_call_targets(op.expression, targets);
            collect_local_call_targets(op.size_expression, targets);
        }
    }
    auto call_target_reaches = [&](const std::string& start, const std::string& goal) {
        std::vector<std::string> pending{start};
        std::set<std::string> visited;
        while (!pending.empty()) {
            const std::string current = std::move(pending.back());
            pending.pop_back();
            if (current == goal) {
                return true;
            }
            if (!visited.insert(current).second) {
                continue;
            }
            auto edges = local_call_graph.find(current);
            if (edges == local_call_graph.end()) {
                continue;
            }
            pending.insert(pending.end(), edges->second.begin(), edges->second.end());
        }
        return false;
    };
    std::set<std::pair<std::string, std::string>> recursive_call_edges;
    for (const auto& caller_edges : local_call_graph) {
        for (const std::string& target : caller_edges.second) {
            if (call_target_reaches(target, caller_edges.first)) {
                recursive_call_edges.emplace(caller_edges.first, target);
            }
        }
    }

    std::vector<ObjExport> exports;
    std::vector<std::string> imports;
    std::map<std::string, int> import_index;
    std::vector<ObjReloc> relocs;
    std::vector<ObjLineRecord> source_lines;
    std::vector<std::uint8_t> code;
    std::vector<VarSlot> data_slots;
    std::vector<ExprTempSlot> expr_temp_slots;
    std::vector<RealSlot> real_slots;
    std::vector<ArraySlot> array_slots;
    std::vector<AddressConstantSlot> address_constant_slots;
    std::set<std::string> data_symbols;
    std::size_t next_expr_temp = 0;
    std::size_t next_real_temp = 0;
    std::size_t next_string_literal = 0;
    std::size_t next_address_constant = 0;
    std::size_t next_control_label = 0;

    auto apply_declaration_binding = [](
        VarSlot slot,
        std::string_view mode,
        std::string_view expression,
        std::size_t line) {
        if (mode == "STORAGE") {
            return slot;
        }
        const ExprValue value = eval_const_expr(expression, builtin_integer_constants());
        if (mode == "INITIAL") {
            const ExprValue minimum = slot.is_signed ? -32768 : 0;
            const ExprValue maximum = slot.is_signed ? 32767 : (slot.is_card ? 0xFFFF : 0xFF);
            if (value < minimum || value > maximum) {
                throw ToolError(
                    "INITIALIZER RANGE LINE " + std::to_string(line) + ": " + slot.name);
            }
            slot.initial_value = static_cast<std::uint16_t>(value);
            return slot;
        }
        if (mode == "ADDRESS") {
            const ExprValue maximum = slot.is_card ? 0xFFFE : 0xFFFF;
            if (value < 0 || value > maximum) {
                throw ToolError(
                    "ADDRESS RANGE LINE " + std::to_string(line) + ": " + slot.name);
            }
            slot.absolute_address = static_cast<std::uint16_t>(value);
            return slot;
        }
        throw ToolError("BAD DECL LINE " + std::to_string(line));
    };

    std::map<std::string, double> real_constants;
    for (const auto& constant : builtin_integer_constants()) {
        real_constants.emplace(constant.first, static_cast<double>(constant.second));
    }
    auto make_real_slot = [&](
        const std::string& name,
        const std::string& prefix,
        std::string_view mode,
        std::string_view expression,
        std::size_t line) {
        RealSlot slot;
        slot.name = upper_ascii(name);
        for (int i = 0; i < 4; ++i) {
            slot.byte_symbols.push_back(prefix + "_B" + std::to_string(i));
        }
        slot.pointer_lo_symbol = prefix + "_PTR_LO";
        slot.pointer_hi_symbol = prefix + "_PTR_HI";
        if (mode == "INITIAL") {
            auto value = try_eval_const_real_expr(expression, real_constants);
            if (!value) {
                throw ToolError(
                    "BAD REAL INITIALIZER LINE " + std::to_string(line) + ": " + slot.name);
            }
            slot.initial_value = real32_bytes(*value);
        } else if (mode == "ADDRESS") {
            const ExprValue address = eval_const_expr(expression, builtin_integer_constants());
            if (address < 0 || address > 0xFFFC) {
                throw ToolError(
                    "ADDRESS RANGE LINE " + std::to_string(line) + ": " + slot.name);
            }
            slot.absolute_address = static_cast<std::uint16_t>(address);
        } else if (mode != "STORAGE") {
            throw ToolError("BAD DECL LINE " + std::to_string(line));
        }
        return slot;
    };

    auto make_array_slot = [&](
        const std::string& name,
        const std::string& prefix,
        std::string_view type_text,
        std::string_view size_expression,
        std::string_view mode_text,
        std::string_view initializer,
        std::size_t line) {
        const std::string type = upper_ascii(type_text);
        const std::string mode = upper_ascii(mode_text);
        const IndexedElementType element_type = indexed_element_type(type);

        ArraySlot slot;
        slot.indexed.pointer = VarSlot{
            upper_ascii(name),
            prefix + "_PTR_LO",
            prefix + "_PTR_HI",
            true,
        };
        slot.indexed.element_type = element_type;
        slot.data_symbol = prefix + "_DATA";
        const std::size_t element_width = slot.indexed.element_width();

        std::optional<std::size_t> element_count;
        if (!trim(size_expression).empty()) {
            const ExprValue count = eval_const_expr(
                size_expression, builtin_integer_constants());
            if (count < 1 ||
                static_cast<unsigned long long>(count) * element_width > 0xFFFFULL) {
                throw ToolError(
                    "ARRAY SIZE RANGE LINE " + std::to_string(line) + ": " +
                    upper_ascii(name));
            }
            element_count = static_cast<std::size_t>(count);
        }

        std::vector<std::uint8_t> initialized;
        if (mode == "STRING") {
            if (type != "BYTE") {
                throw ToolError(
                    "STRING ARRAY TYPE LINE " + std::to_string(line) + ": " +
                    upper_ascii(name));
            }
            const std::string text = trim(initializer);
            if (text.size() < 2 || text.front() != '"' || text.back() != '"') {
                throw ToolError("BAD STRING ARRAY LINE " + std::to_string(line));
            }
            std::string decoded;
            bool escaped = false;
            for (std::size_t i = 1; i + 1 < text.size(); ++i) {
                const char ch = text[i];
                if (escaped) {
                    if (ch == 'n') decoded.push_back('\n');
                    else if (ch == 'r') decoded.push_back('\r');
                    else decoded.push_back(ch);
                    escaped = false;
                } else if (ch == '\\') {
                    escaped = true;
                } else {
                    decoded.push_back(ch);
                }
            }
            if (escaped || decoded.size() > 255) {
                throw ToolError(
                    "STRING SIZE RANGE LINE " + std::to_string(line) + ": " +
                    upper_ascii(name));
            }
            initialized.push_back(static_cast<std::uint8_t>(decoded.size()));
            initialized.insert(initialized.end(), decoded.begin(), decoded.end());
            if (!element_count) {
                element_count = initialized.size();
            }
        } else if (mode == "VALUES") {
            std::vector<std::string> value_expressions;
            if (initializer.find(',') != std::string_view::npos) {
                value_expressions = split_declarators(initializer);
            } else {
                value_expressions = split_words(initializer);
            }
            for (const std::string& value_text : value_expressions) {
                if (slot.indexed.element_is_real()) {
                    auto value = try_eval_const_real_expr(value_text, real_constants);
                    if (!value) {
                        throw ToolError(
                            "BAD REAL ARRAY INITIALIZER LINE " +
                            std::to_string(line) + ": " + upper_ascii(name));
                    }
                    const std::vector<std::uint8_t> bytes = real32_bytes(*value);
                    initialized.insert(initialized.end(), bytes.begin(), bytes.end());
                    continue;
                }
                const ExprValue value = eval_const_expr(
                    value_text, builtin_integer_constants());
                const ExprValue minimum = slot.indexed.element_is_signed() ? -32768 : 0;
                const ExprValue maximum = slot.indexed.element_is_signed()
                    ? 32767
                    : (element_width == 2 ? 0xFFFF : 0xFF);
                if (value < minimum || value > maximum) {
                    throw ToolError(
                        "ARRAY INITIALIZER RANGE LINE " + std::to_string(line) + ": " +
                        upper_ascii(name));
                }
                initialized.push_back(static_cast<std::uint8_t>(value & 0xFF));
                if (element_width == 2) {
                    initialized.push_back(static_cast<std::uint8_t>((value >> 8) & 0xFF));
                }
            }
            if (initialized.empty()) {
                throw ToolError("EMPTY ARRAY INITIALIZER LINE " + std::to_string(line));
            }
            if (!element_count) {
                element_count = initialized.size() / element_width;
            }
        } else if (mode == "ADDRESS") {
            const ExprValue address = eval_const_expr(
                initializer, builtin_integer_constants());
            if (address < 0 || address > 0xFFFF) {
                throw ToolError(
                    "ADDRESS RANGE LINE " + std::to_string(line) + ": " +
                    upper_ascii(name));
            }
            slot.absolute_data_address = static_cast<std::uint16_t>(address);
        } else if (mode != "STORAGE" && mode != "POINTER") {
            throw ToolError("BAD ARRAY DECL LINE " + std::to_string(line));
        }

        if (element_count && !slot.absolute_data_address) {
            const std::size_t byte_count = *element_count * element_width;
            if (initialized.size() > byte_count) {
                throw ToolError(
                    "ARRAY INITIALIZER SIZE LINE " + std::to_string(line) + ": " +
                    upper_ascii(name));
            }
            slot.initial_data.assign(byte_count, 0);
            std::copy(initialized.begin(), initialized.end(), slot.initial_data.begin());
        }
        return slot;
    };

    std::set<std::string> global_names;
    std::map<std::string, VarSlot> global_variables;
    std::map<std::string, RealSlot> global_real_variables;
    std::map<std::string, IndexedSlot> global_arrays;
    std::map<std::string, IndexedSlot> global_pointers;
    struct ReuArrayDeclaration {
        std::string name;
        std::string size_expression;
        std::size_t line = 0;
    };
    std::vector<ReuArrayDeclaration> global_reu_arrays;
    for (const SourceGlobal& declaration : source.globals) {
        const std::string name = upper_ascii(declaration.name);
        if (!global_names.insert(name).second) {
            throw ToolError(
                "DUPLICATE GLOBAL LINE " + std::to_string(declaration.line) + ": " + name);
        }
        const std::string prefix = module + "_" + name;
        if (upper_ascii(declaration.type) == "REU_BYTE_ARRAY") {
            VarSlot slot{
                name,
                prefix + "_LO",
                prefix + "_HI",
                false,
                false,
                0xFF,
            };
            global_variables.emplace(name, slot);
            data_slots.push_back(slot);
            data_symbols.insert(slot.lo_symbol);
            global_reu_arrays.push_back(ReuArrayDeclaration{
                name,
                declaration.expression,
                declaration.line,
            });
            continue;
        }
        const std::string declaration_type = upper_ascii(declaration.type);
        if (declaration_type.size() > 6 &&
            declaration_type.substr(declaration_type.size() - 6) == "_ARRAY") {
            const std::string element_type =
                declaration_type.substr(0, declaration_type.size() - 6);
            ArraySlot slot = make_array_slot(
                name,
                prefix,
                element_type,
                declaration.size_expression,
                declaration.mode,
                declaration.expression,
                declaration.line);
            global_variables.emplace(name, slot.indexed.pointer);
            global_arrays.emplace(name, slot.indexed);
            array_slots.push_back(std::move(slot));
            continue;
        }
        if (declaration_type.size() > 8 &&
            declaration_type.substr(declaration_type.size() - 8) == "_POINTER") {
            const std::string element_type =
                declaration_type.substr(0, declaration_type.size() - 8);
            VarSlot slot = apply_declaration_binding(VarSlot{
                name,
                prefix + "_LO",
                prefix + "_HI",
                true,
            }, declaration.mode, declaration.expression, declaration.line);
            global_variables.emplace(name, slot);
            global_pointers.emplace(name, IndexedSlot{
                slot,
                indexed_element_type(element_type),
            });
            data_slots.push_back(slot);
            data_symbols.insert(slot.lo_symbol);
            continue;
        }
        if (upper_ascii(declaration.type) == "REAL") {
            RealSlot slot = make_real_slot(
                name,
                prefix,
                declaration.mode,
                declaration.expression,
                declaration.line);
            global_real_variables.emplace(name, slot);
            real_slots.push_back(std::move(slot));
            continue;
        }
        VarSlot slot = apply_declaration_binding(VarSlot{
            name,
            prefix + "_LO",
            prefix + "_HI",
            declaration_type == "CARD" || declaration_type == "INT",
            declaration_type == "INT",
        }, declaration.mode, declaration.expression, declaration.line);
        global_variables.emplace(name, slot);
        if (!slot.absolute_address) {
            data_slots.push_back(slot);
            data_symbols.insert(slot.lo_symbol);
        }
    }

    struct ProcedureParameterSlot {
        SourceParameter source;
        std::optional<VarSlot> word;
        std::optional<RealSlot> real;
    };
    struct FunctionReturnSlot {
        std::string type;
        std::optional<RealSlot> real;
    };
    std::map<std::string, std::vector<ProcedureParameterSlot>> procedure_parameters;
    std::map<std::string, FunctionReturnSlot> function_returns;
    for (const SourceProc& proc : ordered) {
        const std::string proc_name = upper_ascii(proc.name);
        if (proc_name == "MAIN" && !proc.parameters.empty()) {
            throw ToolError(
                "MAIN PARAMS LINE " + std::to_string(proc.line));
        }
        std::set<std::string> parameter_names;
        std::vector<ProcedureParameterSlot> slots;
        slots.reserve(proc.parameters.size());
        for (const SourceParameter& parameter : proc.parameters) {
            const std::string name = upper_ascii(parameter.name);
            if (!parameter_names.insert(name).second) {
                throw ToolError(
                    "DUPLICATE PARAM LINE " + std::to_string(proc.line) + ": " + name);
            }
            if (global_names.count(name) != 0) {
                throw ToolError(
                    "PARAM SHADOWS GLOBAL LINE " + std::to_string(proc.line) + ": " + name);
            }
            const std::string type = upper_ascii(parameter.type);
            const std::string prefix = proc_name + "_" + name;
            ProcedureParameterSlot slot;
            slot.source = parameter;
            if (type == "REAL" && !parameter.is_array && !parameter.is_pointer) {
                slot.real = make_real_slot(name, prefix, "STORAGE", "", proc.line);
                real_slots.push_back(*slot.real);
            } else {
                const bool word_value =
                    parameter.is_array || parameter.is_pointer ||
                    type == "CARD" || type == "INT";
                slot.word = VarSlot{
                    name,
                    prefix + "_LO",
                    prefix + "_HI",
                    word_value,
                    type == "INT" && !parameter.is_array && !parameter.is_pointer,
                };
                data_slots.push_back(*slot.word);
                data_symbols.insert(slot.word->lo_symbol);
            }
            slots.push_back(std::move(slot));
        }
        procedure_parameters.emplace(proc_name, std::move(slots));
        if (!proc.return_type.empty()) {
            FunctionReturnSlot result;
            result.type = upper_ascii(proc.return_type);
            if (result.type == "REAL") {
                result.real = make_real_slot(
                    "__RETURN",
                    proc_name + "_RETURN",
                    "STORAGE",
                    "",
                    proc.line);
                real_slots.push_back(*result.real);
            } else if (result.type != "BYTE" && result.type != "CARD" &&
                       result.type != "INT") {
                throw ToolError(
                    "BAD FUNC TYPE LINE " + std::to_string(proc.line));
            }
            function_returns.emplace(proc_name, std::move(result));
        }
    }

    auto add_import = [&](const std::string& symbol) {
        const std::string upper = upper_ascii(symbol);
        auto found = import_index.find(upper);
        if (found == import_index.end()) {
            const int index = static_cast<int>(imports.size());
            found = import_index.emplace(upper, index).first;
            imports.push_back(upper);
        }
        return found->second;
    };

    auto add_reloc = [&](std::uint16_t offset, const std::string& symbol) {
        ObjReloc reloc;
        reloc.offset = offset;
        reloc.symbol = upper_ascii(symbol);
        relocs.push_back(reloc);
    };

    auto add_import_reloc = [&](std::uint16_t offset, const std::string& symbol) {
        ObjReloc reloc;
        reloc.offset = offset;
        reloc.import = true;
        reloc.import_index = add_import(symbol);
        relocs.push_back(reloc);
    };

    auto emit_text = [&](std::string text) {
        text.push_back('\r');
        for (unsigned char ch : text) {
            code.push_back(0xA9);  // LDA #imm
            code.push_back(ch);
            code.push_back(0x20);  // JSR $FFD2 / CHROUT
            code.push_back(0xD2);
            code.push_back(0xFF);
        }
    };

    auto emit_jsr_import = [&](const std::string& symbol) {
        code.push_back(0x20);  // JSR absolute
        const std::uint16_t operand_offset = static_cast<std::uint16_t>(code.size());
        code.push_back(0x00);
        code.push_back(0x00);
        add_import_reloc(operand_offset, symbol);
    };

    auto emit_cr = [&]() {
        code.push_back(0xA9);  // LDA #CR
        code.push_back(0x0D);
        code.push_back(0x20);  // JSR $FFD2 / CHROUT
        code.push_back(0xD2);
        code.push_back(0xFF);
    };

    for (const SourceProc& proc : ordered) {
        std::map<std::string, ExprValue> constants = builtin_integer_constants();
        std::map<std::string, VarSlot> variables = global_variables;
        std::map<std::string, RealSlot> real_variables = global_real_variables;
        std::map<std::string, IndexedSlot> arrays = global_arrays;
        std::map<std::string, IndexedSlot> pointers = global_pointers;
        struct IfFrame {
            bool runtime = false;
            bool active = true;
            bool branch_taken = false;
            bool parent_active = true;
            bool saw_else = false;
            std::string next_label;
            std::string end_label;
        };
        struct ForLoopState {
            VarSlot counter;
            VarSlot step;
            bool descending = false;
        };
        struct LoopFrame {
            bool active = true;
            bool saw_until = false;
            bool has_precondition = false;
            std::size_t if_depth = 0;
            std::string start_label;
            std::string end_label;
            std::optional<ForLoopState> for_loop;
        };
        struct PendingForState {
            bool active = true;
            ParsedForClause clause;
            VarSlot counter;
            VarSlot final_value;
            VarSlot step;
            bool descending = false;
            std::size_t line = 0;
        };
        std::vector<IfFrame> if_stack;
        std::vector<LoopFrame> loop_stack;
        std::optional<std::pair<std::string, std::size_t>> pending_while;
        std::optional<PendingForState> pending_for;
        bool has_value_return = false;
        bool terminal_top_level_return = false;
        for (const SourceOp& op : proc.ops) {
            if (op.kind != SourceOp::Kind::Return) {
                continue;
            }
            if (proc.return_type.empty()) {
                if (!op.value.empty()) {
                    throw ToolError(
                        "PROC RETURN HAS VALUE LINE " + std::to_string(op.line));
                }
            } else {
                if (op.value.empty()) {
                    throw ToolError(
                        "FUNC RETURN VALUE REQUIRED LINE " +
                        std::to_string(op.line));
                }
                has_value_return = true;
            }
        }
        if (!proc.return_type.empty() && !has_value_return) {
            throw ToolError(
                "MISSING FUNC RETURN LINE " + std::to_string(proc.line) +
                ": " + upper_ascii(proc.name));
        }
        const std::uint16_t proc_offset = static_cast<std::uint16_t>(code.size());
        source_lines.push_back(ObjLineRecord{proc_offset, proc.line});
        auto new_control_label = [&](std::string_view purpose) {
            return module + "_" + upper_ascii(proc.name) + "_" + upper_ascii(purpose) + "_" +
                   std::to_string(next_control_label++);
        };
        auto define_control_label = [&](const std::string& label) {
            exports.push_back(ObjExport{
                upper_ascii(label),
                static_cast<std::uint16_t>(code.size()),
                1,
            });
        };
        auto emit_jump = [&](const std::string& label) {
            code.push_back(0x4C);  // JMP absolute
            const std::uint16_t operand_offset = static_cast<std::uint16_t>(code.size());
            code.push_back(0x00);
            code.push_back(0x00);
            add_reloc(operand_offset, label);
        };
        auto variable_symbol = [&](const std::string& variable, std::string_view suffix) {
            return upper_ascii(proc.name) + "_" + upper_ascii(variable) + "_" + std::string(suffix);
        };
        std::set<std::string> local_declarations;
        std::vector<std::string> recursive_frame_symbols;
        std::set<std::string> recursive_frame_symbol_set;
        auto register_recursive_frame_symbol = [&](const std::string& symbol) {
            if (recursive_frame_symbol_set.insert(symbol).second) {
                recursive_frame_symbols.push_back(symbol);
            }
        };
        auto register_recursive_frame_word = [&](const VarSlot& slot) {
            if (slot.absolute_address) {
                return;
            }
            register_recursive_frame_symbol(slot.lo_symbol);
            if (slot.is_card) {
                register_recursive_frame_symbol(slot.hi_symbol);
            }
        };
        auto register_recursive_frame_real = [&](const RealSlot& slot) {
            if (slot.absolute_address) {
                return;
            }
            if (slot.byte_symbols.size() != 4) {
                throw ToolError("BAD REAL SLOT");
            }
            for (const std::string& symbol : slot.byte_symbols) {
                register_recursive_frame_symbol(symbol);
            }
        };
        for (const ProcedureParameterSlot& parameter :
             procedure_parameters.at(upper_ascii(proc.name))) {
            const std::string name = upper_ascii(parameter.source.name);
            local_declarations.insert(name);
            if (parameter.real) {
                real_variables[name] = *parameter.real;
                register_recursive_frame_real(*parameter.real);
                continue;
            }
            if (!parameter.word) {
                throw ToolError("BAD PROC PARAM ABI");
            }
            variables[name] = *parameter.word;
            register_recursive_frame_word(*parameter.word);
            const std::string type = upper_ascii(parameter.source.type);
            const IndexedSlot indexed{
                *parameter.word,
                indexed_element_type(type),
            };
            if (parameter.source.is_array) {
                arrays[name] = indexed;
            } else if (parameter.source.is_pointer) {
                pointers[name] = indexed;
            }
        }
        auto add_variable = [&](
            const std::string& variable,
            bool is_card,
            std::string_view mode = "STORAGE",
            std::string_view expression = "",
            std::size_t line = 0,
            bool is_signed = false) {
            const std::string name = upper_ascii(variable);
            if (!local_declarations.insert(name).second) {
                throw ToolError(
                    "DUPLICATE VAR LINE " + std::to_string(line) + ": " + name);
            }
            if (global_names.find(name) != global_names.end()) {
                throw ToolError(
                    "LOCAL SHADOWS GLOBAL LINE " + std::to_string(line) + ": " + name);
            }
            VarSlot slot = apply_declaration_binding(
                VarSlot{
                    name,
                    variable_symbol(name, "LO"),
                    variable_symbol(name, "HI"),
                    is_card,
                    is_signed,
                },
                mode,
                expression,
                line);
            variables[name] = slot;
            if (!slot.absolute_address && data_symbols.insert(slot.lo_symbol).second) {
                data_slots.push_back(slot);
            }
            register_recursive_frame_word(slot);
        };
        auto add_real_variable = [&](
            const std::string& variable,
            std::string_view mode,
            std::string_view expression,
            std::size_t line) {
            const std::string name = upper_ascii(variable);
            if (!local_declarations.insert(name).second) {
                throw ToolError(
                    "DUPLICATE VAR LINE " + std::to_string(line) + ": " + name);
            }
            if (global_names.find(name) != global_names.end()) {
                throw ToolError(
                    "LOCAL SHADOWS GLOBAL LINE " + std::to_string(line) + ": " + name);
            }
            const std::string prefix = upper_ascii(proc.name) + "_" + name;
            RealSlot slot = make_real_slot(name, prefix, mode, expression, line);
            real_variables[name] = slot;
            register_recursive_frame_real(slot);
            real_slots.push_back(std::move(slot));
        };
        auto add_pointer_variable = [&](
            const std::string& variable,
            std::string_view element_type,
            std::string_view mode,
            std::string_view expression,
            std::size_t line) {
            add_variable(variable, true, mode, expression, line);
            const std::string name = upper_ascii(variable);
            const std::string type = upper_ascii(element_type);
            pointers[name] = IndexedSlot{
                variables.at(name),
                indexed_element_type(type),
            };
        };
        auto add_array_variable = [&](
            const std::string& variable,
            std::string_view element_type,
            std::string_view size_expression,
            std::string_view mode,
            std::string_view expression,
            std::size_t line) {
            const std::string name = upper_ascii(variable);
            if (!local_declarations.insert(name).second) {
                throw ToolError(
                    "DUPLICATE VAR LINE " + std::to_string(line) + ": " + name);
            }
            if (global_names.find(name) != global_names.end()) {
                throw ToolError(
                    "LOCAL SHADOWS GLOBAL LINE " + std::to_string(line) + ": " + name);
            }
            ArraySlot slot = make_array_slot(
                name,
                upper_ascii(proc.name) + "_" + name,
                element_type,
                size_expression,
                mode,
                expression,
                line);
            variables[name] = slot.indexed.pointer;
            arrays[name] = slot.indexed;
            array_slots.push_back(std::move(slot));
        };
        auto expression_uses_variable = [&](std::string_view expr) {
            const std::string upper = upper_ascii(expr);
            for (const auto& item : variables) {
                std::size_t pos = upper.find(item.first);
                while (pos != std::string::npos) {
                    const bool before_ok =
                        pos == 0 ||
                        (!std::isalnum(static_cast<unsigned char>(upper[pos - 1])) && upper[pos - 1] != '_');
                    const std::size_t after = pos + item.first.size();
                    const bool after_ok =
                        after >= upper.size() ||
                        (!std::isalnum(static_cast<unsigned char>(upper[after])) && upper[after] != '_');
                    if (before_ok && after_ok) {
                        return true;
                    }
                    pos = upper.find(item.first, pos + 1);
                }
            }
            return false;
        };
        auto expression_uses_real_variable = [&](std::string_view expr) {
            const std::string upper = upper_ascii(expr);
            for (const auto& item : real_variables) {
                std::size_t pos = upper.find(item.first);
                while (pos != std::string::npos) {
                    const bool before_ok =
                        pos == 0 ||
                        (!std::isalnum(static_cast<unsigned char>(upper[pos - 1])) &&
                         upper[pos - 1] != '_');
                    const std::size_t after = pos + item.first.size();
                    const bool after_ok =
                        after >= upper.size() ||
                        (!std::isalnum(static_cast<unsigned char>(upper[after])) &&
                         upper[after] != '_');
                    if (before_ok && after_ok) {
                        return true;
                    }
                    pos = upper.find(item.first, pos + 1);
                }
            }
            return false;
        };
        auto expression_uses_signed_variable = [&](std::string_view expr) {
            const std::string upper = upper_ascii(expr);
            for (const auto& item : variables) {
                if (!item.second.is_signed) {
                    continue;
                }
                std::size_t pos = upper.find(item.first);
                while (pos != std::string::npos) {
                    const bool before_ok =
                        pos == 0 ||
                        (!std::isalnum(static_cast<unsigned char>(upper[pos - 1])) &&
                         upper[pos - 1] != '_');
                    const std::size_t after = pos + item.first.size();
                    const bool after_ok =
                        after >= upper.size() ||
                        (!std::isalnum(static_cast<unsigned char>(upper[after])) &&
                         upper[after] != '_');
                    if (before_ok && after_ok) {
                        return true;
                    }
                    pos = upper.find(item.first, pos + 1);
                }
            }
            return false;
        };
        auto expression_uses_any_variable = [&](std::string_view expr) {
            return expression_uses_variable(expr) || expression_uses_real_variable(expr);
        };
        auto expression_uses_real_indirect = [&](std::string_view expr) {
            const std::string upper = upper_ascii(expr);
            auto uses = [&](const auto& slots, char suffix) {
                for (const auto& item : slots) {
                    if (!item.second.element_is_real()) {
                        continue;
                    }
                    std::size_t pos = upper.find(item.first);
                    while (pos != std::string::npos) {
                        const bool before_ok =
                            pos == 0 ||
                            (!std::isalnum(static_cast<unsigned char>(upper[pos - 1])) &&
                             upper[pos - 1] != '_');
                        std::size_t after = pos + item.first.size();
                        while (after < upper.size() &&
                               std::isspace(static_cast<unsigned char>(upper[after]))) {
                            ++after;
                        }
                        if (before_ok && after < upper.size() && upper[after] == suffix) {
                            return true;
                        }
                        pos = upper.find(item.first, pos + 1);
                    }
                }
                return false;
            };
            return uses(arrays, '(') || uses(pointers, '^');
        };
        auto expression_looks_real = [&](std::string_view expr) {
            if (expression_uses_real_variable(expr) ||
                expression_uses_real_indirect(expr)) {
                return true;
            }
            const std::string upper = upper_ascii(expr);
            for (const auto& function : function_returns) {
                if (function.second.type != "REAL") {
                    continue;
                }
                std::size_t pos = upper.find(function.first);
                while (pos != std::string::npos) {
                    const bool before_ok =
                        pos == 0 ||
                        (!std::isalnum(static_cast<unsigned char>(upper[pos - 1])) &&
                         upper[pos - 1] != '_');
                    std::size_t after = pos + function.first.size();
                    while (after < upper.size() &&
                           std::isspace(static_cast<unsigned char>(upper[after]))) {
                        ++after;
                    }
                    if (before_ok && after < upper.size() && upper[after] == '(') {
                        return true;
                    }
                    pos = upper.find(function.first, pos + 1);
                }
            }
            if (upper.find("REAL(") != std::string::npos ||
                upper.find("FABS(") != std::string::npos ||
                upper.find("FSQRT(") != std::string::npos ||
                upper.find('.') != std::string::npos) {
                return true;
            }
            return std::regex_search(upper, std::regex("[0-9]E[+-]?[0-9]"));
        };
        auto emit_load_variable = [&](const VarSlot& slot) {
            code.push_back(0xAD);  // LDA absolute
            std::uint16_t operand_offset = static_cast<std::uint16_t>(code.size());
            if (slot.absolute_address) {
                code.push_back(static_cast<std::uint8_t>(*slot.absolute_address & 0xFF));
                code.push_back(static_cast<std::uint8_t>(*slot.absolute_address >> 8));
            } else {
                code.push_back(0x00);
                code.push_back(0x00);
                add_reloc(operand_offset, slot.lo_symbol);
            }
            if (slot.is_card) {
                code.push_back(0xAE);  // LDX absolute
                operand_offset = static_cast<std::uint16_t>(code.size());
                if (slot.absolute_address) {
                    const std::uint16_t high_address =
                        static_cast<std::uint16_t>(*slot.absolute_address + 1);
                    code.push_back(static_cast<std::uint8_t>(high_address & 0xFF));
                    code.push_back(static_cast<std::uint8_t>(high_address >> 8));
                } else {
                    code.push_back(0x00);
                    code.push_back(0x00);
                    add_reloc(operand_offset, slot.hi_symbol);
                }
            } else {
                code.push_back(0xA2);  // LDX #0
                code.push_back(0x00);
            }
        };
        auto emit_store_variable = [&](const VarSlot& slot) {
            code.push_back(0x8D);  // STA absolute
            std::uint16_t operand_offset = static_cast<std::uint16_t>(code.size());
            if (slot.absolute_address) {
                code.push_back(static_cast<std::uint8_t>(*slot.absolute_address & 0xFF));
                code.push_back(static_cast<std::uint8_t>(*slot.absolute_address >> 8));
            } else {
                code.push_back(0x00);
                code.push_back(0x00);
                add_reloc(operand_offset, slot.lo_symbol);
            }
            if (slot.is_card) {
                code.push_back(0x8E);  // STX absolute
                operand_offset = static_cast<std::uint16_t>(code.size());
                if (slot.absolute_address) {
                    const std::uint16_t high_address =
                        static_cast<std::uint16_t>(*slot.absolute_address + 1);
                    code.push_back(static_cast<std::uint8_t>(high_address & 0xFF));
                    code.push_back(static_cast<std::uint8_t>(high_address >> 8));
                } else {
                    code.push_back(0x00);
                    code.push_back(0x00);
                    add_reloc(operand_offset, slot.hi_symbol);
                }
            }
        };
        auto emit_load_immediate = [&](ExprValue value) {
            code.push_back(0xA9);  // LDA #lo
            code.push_back(static_cast<std::uint8_t>(value & 0xFF));
            code.push_back(0xA2);  // LDX #hi
            code.push_back(static_cast<std::uint8_t>((value >> 8) & 0xFF));
        };
        auto allocate_expr_temp = [&]() {
            const std::string prefix =
                upper_ascii(proc.name) + "_EXPR_" + std::to_string(next_expr_temp++);
            ExprTempSlot slot{
                prefix + "_VALUE_LO",
                prefix + "_VALUE_HI",
                prefix + "_POINTER_LO",
                prefix + "_POINTER_HI",
            };
            expr_temp_slots.push_back(slot);
            register_recursive_frame_symbol(slot.value_lo_symbol);
            register_recursive_frame_symbol(slot.value_hi_symbol);
            return slot;
        };
        auto emit_store_word = [&](const ExprTempSlot& slot) {
            code.push_back(0x8D);  // STA absolute
            std::uint16_t operand_offset = static_cast<std::uint16_t>(code.size());
            code.push_back(0x00);
            code.push_back(0x00);
            add_reloc(operand_offset, slot.value_lo_symbol);
            code.push_back(0x8E);  // STX absolute
            operand_offset = static_cast<std::uint16_t>(code.size());
            code.push_back(0x00);
            code.push_back(0x00);
            add_reloc(operand_offset, slot.value_hi_symbol);
        };
        auto emit_load_absolute = [&](const std::string& symbol) {
            code.push_back(0xAD);  // LDA absolute
            const std::uint16_t operand_offset = static_cast<std::uint16_t>(code.size());
            code.push_back(0x00);
            code.push_back(0x00);
            add_reloc(operand_offset, symbol);
        };
        auto emit_store_absolute = [&](const std::string& symbol) {
            code.push_back(0x8D);  // STA absolute
            const std::uint16_t operand_offset = static_cast<std::uint16_t>(code.size());
            code.push_back(0x00);
            code.push_back(0x00);
            add_reloc(operand_offset, symbol);
        };
        std::function<void(std::string_view)> emit_load_word;
        std::function<std::optional<int>(const ParsedCall&)> emit_builtin;
        struct LocalCallResult {
            std::string return_type;
            std::optional<RealSlot> real;
        };
        std::function<std::optional<LocalCallResult>(const ParsedCall&)>
            emit_local_routine_call;
        std::function<RealSlot(std::string_view)> emit_real_expr;
        std::function<void(
            const ParsedExpr&,
            std::size_t,
            const std::map<std::string, ExprValue>&)> emit_expr_node;
        auto emit_load_address_of = [&](const VarSlot& slot) {
            if (slot.absolute_address) {
                emit_load_immediate(*slot.absolute_address);
                return;
            }
            const std::string prefix =
                upper_ascii(proc.name) + "_ADDRESS_" +
                std::to_string(next_address_constant++);
            AddressConstantSlot address{
                prefix + "_LO",
                prefix + "_HI",
                slot.lo_symbol,
            };
            address_constant_slots.push_back(address);
            emit_load_absolute(address.lo_symbol);
            code.push_back(0xAE);  // LDX absolute
            const std::uint16_t operand_offset =
                static_cast<std::uint16_t>(code.size());
            code.push_back(0x00);
            code.push_back(0x00);
            add_reloc(operand_offset, address.hi_symbol);
        };
        auto emit_load_real_address_of = [&](const RealSlot& slot) {
            if (slot.absolute_address) {
                emit_load_immediate(*slot.absolute_address);
                return;
            }
            emit_load_absolute(slot.pointer_lo_symbol);
            code.push_back(0xAE);  // LDX absolute
            const std::uint16_t operand_offset =
                static_cast<std::uint16_t>(code.size());
            code.push_back(0x00);
            code.push_back(0x00);
            add_reloc(operand_offset, slot.pointer_hi_symbol);
        };
        auto emit_prepare_pointer = [&](const IndexedSlot& indexed) {
            emit_load_variable(indexed.pointer);
            code.push_back(0x85);  // STA $0A
            code.push_back(0x0A);
            code.push_back(0x86);  // STX $0B
            code.push_back(0x0B);
        };
        auto emit_add_pointer_byte = [&](
            std::uint8_t opcode,
            const VarSlot& pointer,
            bool high) {
            code.push_back(opcode);
            const std::uint16_t operand_offset =
                static_cast<std::uint16_t>(code.size());
            if (pointer.absolute_address) {
                const std::uint16_t address = static_cast<std::uint16_t>(
                    *pointer.absolute_address + (high ? 1 : 0));
                code.push_back(static_cast<std::uint8_t>(address & 0xFF));
                code.push_back(static_cast<std::uint8_t>(address >> 8));
            } else {
                code.push_back(0x00);
                code.push_back(0x00);
                add_reloc(
                    operand_offset,
                    high ? pointer.hi_symbol : pointer.lo_symbol);
            }
        };
        auto emit_prepare_indexed = [&](
            const IndexedSlot& indexed,
            std::string_view index_expression) {
            emit_load_word(index_expression);
            for (std::size_t width = indexed.element_width(); width > 1; width >>= 1) {
                code.push_back(0x0A);  // ASL A
                code.push_back(0x48);  // PHA
                code.push_back(0x8A);  // TXA
                code.push_back(0x2A);  // ROL A
                code.push_back(0xAA);  // TAX
                code.push_back(0x68);  // PLA
            }
            code.push_back(0x18);  // CLC
            emit_add_pointer_byte(0x6D, indexed.pointer, false);  // ADC pointer low
            code.push_back(0x85);  // STA $0A
            code.push_back(0x0A);
            code.push_back(0x8A);  // TXA
            emit_add_pointer_byte(0x6D, indexed.pointer, true);  // ADC pointer high
            code.push_back(0x85);  // STA $0B
            code.push_back(0x0B);
        };
        auto emit_load_indirect = [&](const IndexedSlot& indexed) {
            if (indexed.element_is_real()) {
                throw ToolError("REAL INDIRECT IN WORD EXPR");
            }
            code.push_back(0xA0);  // LDY #0
            code.push_back(0x00);
            code.push_back(0xB1);  // LDA ($0A),Y
            code.push_back(0x0A);
            if (indexed.element_width() == 2) {
                code.push_back(0x48);  // PHA low
                code.push_back(0xC8);  // INY
                code.push_back(0xB1);  // LDA ($0A),Y
                code.push_back(0x0A);
                code.push_back(0xAA);  // TAX
                code.push_back(0x68);  // PLA low
            } else {
                code.push_back(0xA2);  // LDX #0
                code.push_back(0x00);
            }
        };
        auto emit_store_indirect = [&](
            const IndexedSlot& indexed,
            const ExprTempSlot& value) {
            if (indexed.element_is_real()) {
                throw ToolError("REAL INDIRECT WORD STORE");
            }
            emit_load_absolute(value.value_lo_symbol);
            code.push_back(0xA0);  // LDY #0
            code.push_back(0x00);
            code.push_back(0x91);  // STA ($0A),Y
            code.push_back(0x0A);
            if (indexed.element_width() == 2) {
                code.push_back(0xC8);  // INY
                emit_load_absolute(value.value_hi_symbol);
                code.push_back(0x91);  // STA ($0A),Y
                code.push_back(0x0A);
            }
        };
        auto allocate_string_literal = [&](const std::string& value) {
            if (value.size() > 255) {
                throw ToolError("STRING SIZE RANGE");
            }
            const std::string name =
                "__STRING_" + std::to_string(next_string_literal++);
            const std::string prefix = upper_ascii(proc.name) + "_" + name;
            ArraySlot slot;
            slot.indexed.pointer = VarSlot{
                name,
                prefix + "_PTR_LO",
                prefix + "_PTR_HI",
                true,
            };
            slot.data_symbol = prefix + "_DATA";
            slot.initial_data.push_back(static_cast<std::uint8_t>(value.size()));
            slot.initial_data.insert(
                slot.initial_data.end(), value.begin(), value.end());
            const VarSlot pointer = slot.indexed.pointer;
            array_slots.push_back(std::move(slot));
            return pointer;
        };
        emit_expr_node = [&](const ParsedExpr& expr,
                             std::size_t index,
                             const std::map<std::string, ExprValue>& fold_constants) {
            if (auto value = evaluate_expr_node(expr, index, fold_constants)) {
                emit_load_immediate(*value);
                return;
            }

            const ExprNode& node = expr.nodes.at(index);
            if (node.kind == ExprNode::Kind::StringLiteral) {
                emit_load_variable(allocate_string_literal(node.name));
                return;
            }
            if (node.kind == ExprNode::Kind::Variable) {
                auto variable = variables.find(node.name);
                if (variable == variables.end()) {
                    throw ToolError("UNKNOWN VAR");
                }
                emit_load_variable(variable->second);
                return;
            }
            if (node.kind == ExprNode::Kind::AddressOf) {
                const ExprNode& target = expr.nodes.at(node.left);
                if (target.kind != ExprNode::Kind::Variable) {
                    throw ToolError("BAD ADDRESS EXPR");
                }
                auto variable = variables.find(target.name);
                if (variable != variables.end()) {
                    emit_load_address_of(variable->second);
                    return;
                }
                auto real_variable = real_variables.find(target.name);
                if (real_variable != real_variables.end()) {
                    emit_load_real_address_of(real_variable->second);
                    return;
                }
                throw ToolError("UNKNOWN VAR");
            }
            if (node.kind == ExprNode::Kind::Dereference) {
                auto pointer = pointers.find(node.name);
                if (pointer == pointers.end()) {
                    throw ToolError("UNKNOWN POINTER " + node.name);
                }
                emit_prepare_pointer(pointer->second);
                emit_load_indirect(pointer->second);
                return;
            }
            if (node.kind == ExprNode::Kind::Call) {
                auto array = arrays.find(node.name);
                if (array != arrays.end()) {
                    if (node.arguments.size() != 1) {
                        throw ToolError("BAD ARRAY INDEX " + node.name);
                    }
                    emit_prepare_indexed(array->second, node.arguments.front());
                    emit_load_indirect(array->second);
                    return;
                }
                auto return_width = emit_builtin(ParsedCall{node.name, node.arguments});
                if (return_width) {
                    if (*return_width == 0) {
                        throw ToolError("PROC HAS NO VALUE " + node.name);
                    }
                    return;
                }
                auto local_result = emit_local_routine_call(
                    ParsedCall{node.name, node.arguments});
                if (!local_result) {
                    throw ToolError("UNSUPPORTED CALL " + node.name);
                }
                if (local_result->return_type.empty()) {
                    throw ToolError("PROC HAS NO VALUE " + node.name);
                }
                if (local_result->return_type == "REAL") {
                    throw ToolError("REAL FUNC IN WORD EXPR " + node.name);
                }
                return;
            }
            if (node.kind == ExprNode::Kind::Negate) {
                emit_expr_node(expr, node.left, fold_constants);
                code.push_back(0x49);  // EOR #$FF
                code.push_back(0xFF);
                code.push_back(0x18);  // CLC
                code.push_back(0x69);  // ADC #1
                code.push_back(0x01);
                code.push_back(0x48);  // PHA
                code.push_back(0x8A);  // TXA
                code.push_back(0x49);  // EOR #$FF
                code.push_back(0xFF);
                code.push_back(0x69);  // ADC #0 with carry from low byte
                code.push_back(0x00);
                code.push_back(0xAA);  // TAX
                code.push_back(0x68);  // PLA
                return;
            }
            if (node.kind == ExprNode::Kind::Constant) {
                emit_load_immediate(node.value);
                return;
            }

            if (node.kind == ExprNode::Kind::Add || node.kind == ExprNode::Kind::Subtract) {
                const bool subtract = node.kind == ExprNode::Kind::Subtract;
                auto emit_add_sub_high = [&](bool absolute, const std::string& symbol, ExprValue value) {
                    code.push_back(subtract ? (absolute ? 0xED : 0xE9)
                                            : (absolute ? 0x6D : 0x69));
                    if (absolute) {
                        const std::uint16_t operand_offset = static_cast<std::uint16_t>(code.size());
                        code.push_back(0x00);
                        code.push_back(0x00);
                        add_reloc(operand_offset, symbol);
                    } else {
                        code.push_back(static_cast<std::uint8_t>((value >> 8) & 0xFF));
                    }
                };
                if (auto rhs_value = evaluate_expr_node(expr, node.right, fold_constants)) {
                    emit_expr_node(expr, node.left, fold_constants);
                    code.push_back(subtract ? 0x38 : 0x18);  // SEC/CLC
                    code.push_back(subtract ? 0xE9 : 0x69);  // SBC/ADC immediate low
                    code.push_back(static_cast<std::uint8_t>(*rhs_value & 0xFF));
                    code.push_back(0x48);  // PHA
                    code.push_back(0x8A);  // TXA
                    emit_add_sub_high(false, {}, *rhs_value);
                    code.push_back(0xAA);  // TAX
                    code.push_back(0x68);  // PLA
                    return;
                }
                const ExprNode& rhs_node = expr.nodes.at(node.right);
                if (rhs_node.kind == ExprNode::Kind::Variable) {
                    auto rhs_variable = variables.find(rhs_node.name);
                    if (rhs_variable != variables.end()) {
                        emit_expr_node(expr, node.left, fold_constants);
                        code.push_back(subtract ? 0x38 : 0x18);  // SEC/CLC
                        code.push_back(subtract ? 0xED : 0x6D);  // SBC/ADC absolute low
                        std::uint16_t operand_offset = static_cast<std::uint16_t>(code.size());
                        if (rhs_variable->second.absolute_address) {
                            code.push_back(static_cast<std::uint8_t>(
                                *rhs_variable->second.absolute_address & 0xFF));
                            code.push_back(static_cast<std::uint8_t>(
                                *rhs_variable->second.absolute_address >> 8));
                        } else {
                            code.push_back(0x00);
                            code.push_back(0x00);
                            add_reloc(operand_offset, rhs_variable->second.lo_symbol);
                        }
                        code.push_back(0x48);  // PHA
                        code.push_back(0x8A);  // TXA
                        if (rhs_variable->second.is_card) {
                            code.push_back(subtract ? 0xED : 0x6D);  // SBC/ADC absolute high
                            operand_offset = static_cast<std::uint16_t>(code.size());
                            if (rhs_variable->second.absolute_address) {
                                const std::uint16_t high_address = static_cast<std::uint16_t>(
                                    *rhs_variable->second.absolute_address + 1);
                                code.push_back(static_cast<std::uint8_t>(high_address & 0xFF));
                                code.push_back(static_cast<std::uint8_t>(high_address >> 8));
                            } else {
                                code.push_back(0x00);
                                code.push_back(0x00);
                                add_reloc(operand_offset, rhs_variable->second.hi_symbol);
                            }
                        } else {
                            emit_add_sub_high(false, {}, 0);
                        }
                        code.push_back(0xAA);  // TAX
                        code.push_back(0x68);  // PLA
                        return;
                    }
                }
            }

            const ExprTempSlot temp = allocate_expr_temp();
            emit_expr_node(expr, node.right, fold_constants);
            emit_store_word(temp);
            emit_expr_node(expr, node.left, fold_constants);

            if (node.kind == ExprNode::Kind::Add || node.kind == ExprNode::Kind::Subtract) {
                const bool subtract = node.kind == ExprNode::Kind::Subtract;
                code.push_back(subtract ? 0x38 : 0x18);  // SEC/CLC
                code.push_back(subtract ? 0xED : 0x6D);  // SBC/ADC absolute low
                std::uint16_t operand_offset = static_cast<std::uint16_t>(code.size());
                code.push_back(0x00);
                code.push_back(0x00);
                add_reloc(operand_offset, temp.value_lo_symbol);
                code.push_back(0x48);  // PHA
                code.push_back(0x8A);  // TXA
                code.push_back(subtract ? 0xED : 0x6D);  // SBC/ADC absolute high
                operand_offset = static_cast<std::uint16_t>(code.size());
                code.push_back(0x00);
                code.push_back(0x00);
                add_reloc(operand_offset, temp.value_hi_symbol);
                code.push_back(0xAA);  // TAX
                code.push_back(0x68);  // PLA
                return;
            }

            // RT_I_MUL and RT_I_DIV take the left word in A/X and a pointer to
            // the right word in zero-page $02/$03, returning the result in A/X.
            code.push_back(0x48);  // PHA low
            code.push_back(0x8A);  // TXA
            code.push_back(0x48);  // PHA high
            emit_load_absolute(temp.pointer_lo_symbol);
            code.push_back(0x85);  // STA $02
            code.push_back(0x02);
            emit_load_absolute(temp.pointer_hi_symbol);
            code.push_back(0x85);  // STA $03
            code.push_back(0x03);
            code.push_back(0x68);  // PLA high
            code.push_back(0xAA);  // TAX
            code.push_back(0x68);  // PLA low
            emit_jsr_import(
                node.kind == ExprNode::Kind::Multiply ? "RT_I_MUL" : "RT_I_DIV");
        };
        emit_load_word = [&](std::string_view text) {
            const ParsedExpr expr = WordExprParser(text).parse();
            std::map<std::string, ExprValue> fold_constants = constants;
            for (const auto& variable : variables) {
                fold_constants.erase(variable.first);
            }
            emit_expr_node(expr, expr.root, fold_constants);
        };
        auto emit_real_byte_access = [&](
            std::uint8_t opcode,
            const RealSlot& slot,
            std::size_t index) {
            if (index >= 4 || slot.byte_symbols.size() != 4) {
                throw ToolError("BAD REAL SLOT");
            }
            code.push_back(opcode);
            const std::uint16_t operand_offset = static_cast<std::uint16_t>(code.size());
            if (slot.absolute_address) {
                const std::uint16_t address = static_cast<std::uint16_t>(
                    *slot.absolute_address + static_cast<std::uint16_t>(index));
                code.push_back(static_cast<std::uint8_t>(address & 0xFF));
                code.push_back(static_cast<std::uint8_t>(address >> 8));
            } else {
                code.push_back(0x00);
                code.push_back(0x00);
                add_reloc(operand_offset, slot.byte_symbols[index]);
            }
        };
        auto emit_load_real_indirect = [&](const RealSlot& destination) {
            for (std::size_t i = 0; i < 4; ++i) {
                code.push_back(0xA0);  // LDY #element byte
                code.push_back(static_cast<std::uint8_t>(i));
                code.push_back(0xB1);  // LDA ($0A),Y
                code.push_back(0x0A);
                emit_real_byte_access(0x8D, destination, i);  // STA absolute
            }
        };
        auto emit_store_real_indirect = [&](const RealSlot& source) {
            for (std::size_t i = 0; i < 4; ++i) {
                emit_real_byte_access(0xAD, source, i);  // LDA absolute
                code.push_back(0xA0);  // LDY #element byte
                code.push_back(static_cast<std::uint8_t>(i));
                code.push_back(0x91);  // STA ($0A),Y
                code.push_back(0x0A);
            }
        };
        auto emit_real_copy = [&](const RealSlot& source, const RealSlot& destination) {
            if (source.pointer_lo_symbol == destination.pointer_lo_symbol) {
                return;
            }
            for (std::size_t i = 0; i < 4; ++i) {
                emit_real_byte_access(0xAD, source, i);  // LDA absolute
                emit_real_byte_access(0x8D, destination, i);  // STA absolute
            }
        };
        auto emit_set_real_pointer = [&](const RealSlot& slot, std::uint8_t zero_page) {
            emit_load_absolute(slot.pointer_lo_symbol);
            code.push_back(0x85);  // STA zero page
            code.push_back(zero_page);
            emit_load_absolute(slot.pointer_hi_symbol);
            code.push_back(0x85);  // STA zero page
            code.push_back(static_cast<std::uint8_t>(zero_page + 1));
        };
        auto allocate_real_temp = [&](std::optional<double> initial = std::nullopt) {
            const std::string name =
                "__REAL_TEMP_" + std::to_string(next_real_temp++);
            RealSlot slot = make_real_slot(
                name,
                upper_ascii(proc.name) + "_" + name,
                "STORAGE",
                "",
                0);
            if (initial) {
                slot.initial_value = real32_bytes(*initial);
            }
            register_recursive_frame_real(slot);
            real_slots.push_back(slot);
            return slot;
        };
        auto emit_prepared_indirect_as_real = [&](const IndexedSlot& indexed) {
            RealSlot destination = allocate_real_temp();
            if (indexed.element_is_real()) {
                emit_load_real_indirect(destination);
                return destination;
            }
            emit_load_indirect(indexed);
            emit_set_real_pointer(destination, 0x02);
            emit_jsr_import(
                indexed.element_is_signed() ? "RT_S_TO_F" : "RT_I_TO_F");
            return destination;
        };
        std::function<RealSlot(const ParsedRealExpr&, std::size_t)> emit_real_expr_node;
        emit_real_expr_node = [&](const ParsedRealExpr& expr, std::size_t index) -> RealSlot {
            if (auto value = evaluate_real_expr_node(expr, index, real_constants)) {
                return allocate_real_temp(*value);
            }

            const RealExprNode& node = expr.nodes.at(index);
            if (node.kind == RealExprNode::Kind::Variable) {
                auto real_variable = real_variables.find(node.name);
                if (real_variable != real_variables.end()) {
                    return real_variable->second;
                }
                auto integer_variable = variables.find(node.name);
                if (integer_variable == variables.end()) {
                    throw ToolError("UNKNOWN REAL VAR " + node.name);
                }
                RealSlot destination = allocate_real_temp();
                emit_set_real_pointer(destination, 0x02);
                emit_load_variable(integer_variable->second);
                emit_jsr_import(
                    integer_variable->second.is_signed ? "RT_S_TO_F" : "RT_I_TO_F");
                return destination;
            }
            if (node.kind == RealExprNode::Kind::Dereference) {
                auto pointer = pointers.find(node.name);
                if (pointer == pointers.end()) {
                    throw ToolError("UNKNOWN POINTER " + node.name);
                }
                emit_prepare_pointer(pointer->second);
                return emit_prepared_indirect_as_real(pointer->second);
            }
            if (node.kind == RealExprNode::Kind::Call) {
                const ParsedCall call{node.name, node.arguments};
                auto array = arrays.find(node.name);
                if (array != arrays.end()) {
                    if (node.arguments.size() != 1) {
                        throw ToolError("BAD ARRAY INDEX " + node.name);
                    }
                    emit_prepare_indexed(array->second, node.arguments.front());
                    return emit_prepared_indirect_as_real(array->second);
                }
                if (auto return_width = emit_builtin(call)) {
                    if (*return_width == 0) {
                        throw ToolError("PROC HAS NO VALUE " + node.name);
                    }
                    RealSlot destination = allocate_real_temp();
                    emit_set_real_pointer(destination, 0x02);
                    emit_jsr_import("RT_I_TO_F");
                    return destination;
                }
                auto local_result = emit_local_routine_call(call);
                if (!local_result) {
                    throw ToolError("UNSUPPORTED REAL CALL " + node.name);
                }
                if (local_result->return_type.empty()) {
                    throw ToolError("PROC HAS NO VALUE " + node.name);
                }
                RealSlot destination = allocate_real_temp();
                if (local_result->return_type == "REAL") {
                    if (!local_result->real) {
                        throw ToolError("BAD FUNC ABI " + node.name);
                    }
                    emit_real_copy(*local_result->real, destination);
                } else {
                    emit_set_real_pointer(destination, 0x02);
                    emit_jsr_import(
                        local_result->return_type == "INT"
                            ? "RT_S_TO_F"
                            : "RT_I_TO_F");
                }
                return destination;
            }

            const RealSlot lhs = emit_real_expr_node(expr, node.left);
            if (node.kind == RealExprNode::Kind::Cast) {
                return lhs;
            }
            RealSlot destination = allocate_real_temp();
            if (node.kind == RealExprNode::Kind::Negate) {
                emit_real_copy(lhs, destination);
                emit_real_byte_access(0xAD, destination, 3);  // LDA absolute
                code.push_back(0x49);  // EOR #$80
                code.push_back(0x80);
                emit_real_byte_access(0x8D, destination, 3);  // STA absolute
                return destination;
            }
            if (node.kind == RealExprNode::Kind::Absolute ||
                node.kind == RealExprNode::Kind::SquareRoot) {
                emit_set_real_pointer(lhs, 0x02);
                emit_set_real_pointer(destination, 0x06);
                emit_jsr_import(
                    node.kind == RealExprNode::Kind::Absolute ? "RT_F_ABS" : "RT_F_SQRT");
                return destination;
            }

            const RealSlot rhs = emit_real_expr_node(expr, node.right);
            emit_set_real_pointer(lhs, 0x02);
            emit_set_real_pointer(rhs, 0x04);
            emit_set_real_pointer(destination, 0x06);
            std::string helper;
            if (node.kind == RealExprNode::Kind::Add) {
                helper = "RT_F_ADD";
            } else if (node.kind == RealExprNode::Kind::Subtract) {
                helper = "RT_F_SUB";
            } else if (node.kind == RealExprNode::Kind::Multiply) {
                helper = "RT_F_MUL";
            } else if (node.kind == RealExprNode::Kind::Divide) {
                helper = "RT_F_DIV";
            } else {
                throw ToolError("BAD REAL EXPR");
            }
            emit_jsr_import(helper);
            return destination;
        };
        emit_real_expr = [&](std::string_view text) {
            const ParsedRealExpr expr = RealExprParser(text).parse();
            return emit_real_expr_node(expr, expr.root);
        };
        auto emit_load_index_absolute = [&](std::uint8_t opcode, const std::string& symbol) {
            code.push_back(opcode);
            const std::uint16_t operand_offset = static_cast<std::uint16_t>(code.size());
            code.push_back(0x00);
            code.push_back(0x00);
            add_reloc(operand_offset, symbol);
        };
        emit_builtin = [&](const ParsedCall& call) -> std::optional<int> {
            auto spec = builtin_call(call.name);
            if (!spec) {
                return std::nullopt;
            }
            if (call.arguments.size() != spec->arguments.size()) {
                throw ToolError("BAD CALL " + call.name);
            }

            std::vector<ExprTempSlot> argument_slots;
            argument_slots.reserve(call.arguments.size());
            for (const std::string& argument : call.arguments) {
                ExprTempSlot slot = allocate_expr_temp();
                emit_load_word(argument);
                emit_store_word(slot);
                argument_slots.push_back(std::move(slot));
            }

            for (std::size_t i = 0; i < argument_slots.size(); ++i) {
                std::optional<std::uint8_t> zero_page;
                if (spec->arguments[i] == CallRegister::ZeroPage0E) {
                    zero_page = 0x0E;
                } else if (spec->arguments[i] == CallRegister::ZeroPageE0) {
                    zero_page = 0xE0;
                }
                if (!zero_page) {
                    continue;
                }
                emit_load_absolute(argument_slots[i].value_lo_symbol);
                code.push_back(0x85);  // STA zero page
                code.push_back(*zero_page);
                emit_load_absolute(argument_slots[i].value_hi_symbol);
                code.push_back(0x85);  // STA zero page
                code.push_back(static_cast<std::uint8_t>(*zero_page + 1));
            }

            // Load index registers first so the final A load cannot be clobbered.
            for (std::size_t i = 0; i < argument_slots.size(); ++i) {
                const ExprTempSlot& slot = argument_slots[i];
                if (spec->arguments[i] == CallRegister::X ||
                    spec->arguments[i] == CallRegister::XY) {
                    emit_load_index_absolute(0xAE, slot.value_lo_symbol);  // LDX absolute
                }
                if (spec->arguments[i] == CallRegister::Y) {
                    emit_load_index_absolute(0xAC, slot.value_lo_symbol);  // LDY absolute
                } else if (spec->arguments[i] == CallRegister::XY) {
                    emit_load_index_absolute(0xAC, slot.value_hi_symbol);  // LDY absolute
                }
            }
            if (spec->carry_low_bit_argument >= 0) {
                const std::size_t carry_index =
                    static_cast<std::size_t>(spec->carry_low_bit_argument);
                if (carry_index >= argument_slots.size()) {
                    throw ToolError("BAD CALL ABI " + call.name);
                }
                emit_load_absolute(argument_slots[carry_index].value_hi_symbol);
                code.push_back(0x4A);  // LSR A: bit 0 becomes carry
            }
            for (std::size_t i = 0; i < argument_slots.size(); ++i) {
                if (spec->arguments[i] == CallRegister::A) {
                    emit_load_absolute(argument_slots[i].value_lo_symbol);
                }
            }
            emit_jsr_import(spec->helper);
            if (spec->return_width == 1) {
                code.push_back(0xA2);  // LDX #0 for a BYTE result
                code.push_back(0x00);
            }
            return spec->return_width;
        };
        emit_local_routine_call = [&](const ParsedCall& call)
            -> std::optional<LocalCallResult> {
            const std::string target = upper_ascii(call.name);
            const bool recursive_call = recursive_call_edges.count(
                {upper_ascii(proc.name), target}) != 0;
            auto abi = procedure_parameters.find(target);
            if (abi == procedure_parameters.end()) {
                return std::nullopt;
            }
            if (call.arguments.size() != abi->second.size()) {
                throw ToolError("BAD CALL " + target);
            }

            struct StagedParameter {
                std::optional<ExprTempSlot> word;
                std::optional<RealSlot> real;
            };
            std::vector<StagedParameter> staged;
            staged.reserve(call.arguments.size());
            for (std::size_t i = 0; i < call.arguments.size(); ++i) {
                StagedParameter value;
                if (abi->second[i].real) {
                    value.real = emit_real_expr(call.arguments[i]);
                } else {
                    ExprTempSlot temp = allocate_expr_temp();
                    emit_load_word(call.arguments[i]);
                    emit_store_word(temp);
                    value.word = std::move(temp);
                }
                staged.push_back(std::move(value));
            }

            if (recursive_call) {
                for (const std::string& symbol : recursive_frame_symbols) {
                    emit_load_absolute(symbol);
                    code.push_back(0x48);  // PHA caller-frame byte
                }
            }

            for (std::size_t i = 0; i < staged.size(); ++i) {
                const ProcedureParameterSlot& parameter = abi->second[i];
                if (parameter.real) {
                    if (!staged[i].real) {
                        throw ToolError("BAD CALL ABI " + target);
                    }
                    emit_real_copy(*staged[i].real, *parameter.real);
                    continue;
                }
                if (!parameter.word || !staged[i].word) {
                    throw ToolError("BAD CALL ABI " + target);
                }
                emit_load_absolute(staged[i].word->value_lo_symbol);
                if (parameter.word->is_card) {
                    emit_load_index_absolute(
                        0xAE, staged[i].word->value_hi_symbol);  // LDX absolute
                } else {
                    code.push_back(0xA2);  // LDX #0
                    code.push_back(0x00);
                }
                emit_store_variable(*parameter.word);
            }

            code.push_back(0x20);  // JSR local procedure
            const std::uint16_t operand_offset =
                static_cast<std::uint16_t>(code.size());
            code.push_back(0x00);
            code.push_back(0x00);
            add_reloc(operand_offset, target);
            LocalCallResult result;
            auto function = function_returns.find(target);
            const bool preserve_word_result =
                function != function_returns.end() && function->second.type != "REAL";
            if (recursive_call && !recursive_frame_symbols.empty()) {
                if (preserve_word_result) {
                    code.push_back(0xA8);  // TAY preserves the result low byte.
                }
                for (auto symbol = recursive_frame_symbols.rbegin();
                     symbol != recursive_frame_symbols.rend(); ++symbol) {
                    code.push_back(0x68);  // PLA caller-frame byte
                    emit_store_absolute(*symbol);
                }
                if (preserve_word_result) {
                    code.push_back(0x98);  // TYA restores the result low byte.
                }
            }
            if (function != function_returns.end()) {
                result.return_type = function->second.type;
                result.real = function->second.real;
            }
            return result;
        };
        auto emit_reu_allocation = [&](
            const VarSlot& handle,
            std::string_view size_expression,
            std::size_t line) {
            auto size = try_eval_const_expr(size_expression, constants);
            if (!size) {
                throw ToolError(
                    "REU SIZE MUST BE CONSTANT LINE " + std::to_string(line));
            }
            if (*size < 1 || *size > 0xFFFF) {
                throw ToolError(
                    "REU SIZE RANGE LINE " + std::to_string(line) + ": " + handle.name);
            }
            emit_load_immediate(*size);
            emit_jsr_import("RT_REU_ALLOC");
            code.push_back(0xA2);  // BYTE handle result
            code.push_back(0x00);
            emit_store_variable(handle);
            constants.erase(handle.name);
        };
        if (upper_ascii(proc.name) == "MAIN") {
            for (const ReuArrayDeclaration& declaration : global_reu_arrays) {
                emit_reu_allocation(
                    variables.at(declaration.name),
                    declaration.size_expression,
                    declaration.line);
            }
        }
        auto emit_branch = [&](std::uint8_t opcode) {
            code.push_back(opcode);
            const std::size_t operand = code.size();
            code.push_back(0x00);
            return operand;
        };
        auto patch_branch_to_current = [&](std::size_t operand) {
            const std::ptrdiff_t delta = static_cast<std::ptrdiff_t>(code.size()) -
                                         static_cast<std::ptrdiff_t>(operand + 1);
            if (delta < -128 || delta > 127) {
                throw ToolError("INTERNAL BRANCH RANGE");
            }
            code[operand] = static_cast<std::uint8_t>(static_cast<int>(delta) & 0xFF);
        };
        auto patch_branch_to_offset = [&](std::size_t operand, std::size_t target) {
            const std::ptrdiff_t delta = static_cast<std::ptrdiff_t>(target) -
                                         static_cast<std::ptrdiff_t>(operand + 1);
            if (delta < -128 || delta > 127) {
                throw ToolError("INTERNAL BRANCH RANGE");
            }
            code[operand] = static_cast<std::uint8_t>(static_cast<int>(delta) & 0xFF);
        };
        auto emit_action_string = [&](std::string_view expression) {
            emit_load_word(expression);
            code.push_back(0x85);  // STA $0A
            code.push_back(0x0A);
            code.push_back(0x86);  // STX $0B
            code.push_back(0x0B);
            code.push_back(0xA0);  // LDY #0
            code.push_back(0x00);
            code.push_back(0xB1);  // LDA ($0A),Y: Action string length
            code.push_back(0x0A);
            code.push_back(0xAA);  // TAX
            const std::size_t empty = emit_branch(0xF0);  // BEQ done
            const std::size_t loop = code.size();
            code.push_back(0xC8);  // INY
            code.push_back(0xB1);  // LDA ($0A),Y
            code.push_back(0x0A);
            code.push_back(0x20);  // JSR CHROUT
            code.push_back(0xD2);
            code.push_back(0xFF);
            code.push_back(0xCA);  // DEX
            const std::size_t again = emit_branch(0xD0);  // BNE loop
            patch_branch_to_offset(again, loop);
            patch_branch_to_current(empty);
            emit_cr();
        };
        auto emit_compare_absolute = [&](const std::string& symbol) {
            code.push_back(0xCD);  // CMP absolute
            const std::uint16_t operand_offset = static_cast<std::uint16_t>(code.size());
            code.push_back(0x00);
            code.push_back(0x00);
            add_reloc(operand_offset, symbol);
        };
        auto compare_known_out_of_range = [](
            std::string_view op,
            bool is_card,
            bool is_signed,
            ExprValue rhs_value) -> std::optional<bool> {
            const ExprValue min_value = is_signed ? -32768 : 0;
            const ExprValue max_value = is_signed ? 32767 : (is_card ? 0xFFFF : 0xFF);
            if (rhs_value >= min_value && rhs_value <= max_value) {
                return std::nullopt;
            }
            const bool below = rhs_value < min_value;
            if (op == "=") return false;
            if (op == "<>") return true;
            if (op == "<") return !below;
            if (op == "<=") return !below;
            if (op == ">") return below;
            if (op == ">=") return below;
            return std::nullopt;
        };
        auto try_eval_real_condition = [&](std::string_view condition) -> std::optional<bool> {
            try {
                if (auto comparison = parse_comparison(condition)) {
                    auto lhs = try_eval_const_real_expr(comparison->lhs, real_constants);
                    auto rhs = try_eval_const_real_expr(comparison->rhs, real_constants);
                    if (!lhs || !rhs) {
                        return std::nullopt;
                    }
                    if (comparison->op == "=") return *lhs == *rhs;
                    if (comparison->op == "<>") return *lhs != *rhs;
                    if (comparison->op == "<") return *lhs < *rhs;
                    if (comparison->op == "<=") return *lhs <= *rhs;
                    if (comparison->op == ">") return *lhs > *rhs;
                    if (comparison->op == ">=") return *lhs >= *rhs;
                    return std::nullopt;
                }
                auto value = try_eval_const_real_expr(condition, real_constants);
                return value ? std::optional<bool>(*value != 0.0) : std::nullopt;
            } catch (const ToolError&) {
                return std::nullopt;
            }
        };
        auto emit_real_condition_false_jump = [&](
            std::string_view condition,
            const std::string& false_label) {
            ParsedComparison comparison;
            if (auto parsed = parse_comparison(condition)) {
                comparison = std::move(*parsed);
            } else {
                comparison = ParsedComparison{
                    strip_outer_condition_parentheses(std::string(condition)),
                    "<>",
                    "0.0",
                };
            }
            const RealSlot lhs = emit_real_expr(comparison.lhs);
            const RealSlot rhs = emit_real_expr(comparison.rhs);
            emit_set_real_pointer(lhs, 0x02);
            emit_set_real_pointer(rhs, 0x04);
            emit_jsr_import("RT_F_CMP");

            std::uint8_t compare_value = 0;
            std::uint8_t true_branch = 0;
            if (comparison.op == "=") {
                compare_value = 0x00;
                true_branch = 0xF0;  // BEQ
            } else if (comparison.op == "<>") {
                compare_value = 0x00;
                true_branch = 0xD0;  // BNE
            } else if (comparison.op == "<") {
                compare_value = 0xFF;
                true_branch = 0xF0;  // BEQ
            } else if (comparison.op == "<=") {
                compare_value = 0x01;
                true_branch = 0xD0;  // BNE
            } else if (comparison.op == ">") {
                compare_value = 0x01;
                true_branch = 0xF0;  // BEQ
            } else if (comparison.op == ">=") {
                compare_value = 0xFF;
                true_branch = 0xD0;  // BNE
            } else {
                throw ToolError("BAD REAL CONDITION");
            }
            code.push_back(0xC9);  // CMP immediate
            code.push_back(compare_value);
            const std::size_t true_operand = emit_branch(true_branch);
            emit_jump(false_label);
            patch_branch_to_current(true_operand);
        };
        auto emit_condition_false_jump = [&](std::string_view condition, const std::string& false_label) {
            if (expression_looks_real(condition)) {
                if (!expression_uses_any_variable(condition)) {
                    auto value = try_eval_real_condition(condition);
                    if (!value) {
                        throw ToolError("BAD REAL CONDITION");
                    }
                    if (!*value) {
                        emit_jump(false_label);
                    }
                } else {
                    emit_real_condition_false_jump(condition, false_label);
                }
                return;
            }
            if (!expression_uses_variable(condition)) {
                auto value = try_eval_const_condition(condition, constants);
                if (!value) {
                    throw ToolError("BAD CONDITION");
                }
                if (!*value) {
                    emit_jump(false_label);
                }
                return;
            }

            ParsedComparison comparison;
            if (auto parsed = parse_comparison(condition)) {
                comparison = std::move(*parsed);
            } else {
                comparison = ParsedComparison{
                    strip_outer_condition_parentheses(std::string(condition)),
                    "<>",
                    "0",
                };
            }

            auto simple_lhs = variables.find(upper_ascii(comparison.lhs));
            if (simple_lhs != variables.end() && !expression_uses_variable(comparison.rhs)) {
                if (auto rhs_value = try_eval_const_expr(comparison.rhs, constants)) {
                    if (auto known = compare_known_out_of_range(
                            comparison.op,
                            simple_lhs->second.is_card,
                            simple_lhs->second.is_signed,
                            *rhs_value)) {
                        if (!*known) {
                            emit_jump(false_label);
                        }
                        return;
                    }
                }
            }

            const ExprTempSlot lhs_slot = allocate_expr_temp();
            const ExprTempSlot rhs_slot = allocate_expr_temp();
            emit_load_word(comparison.lhs);
            emit_store_word(lhs_slot);
            emit_load_word(comparison.rhs);
            emit_store_word(rhs_slot);

            std::vector<std::size_t> true_branches;
            std::vector<std::size_t> false_branches;
            const bool signed_comparison =
                expression_uses_signed_variable(comparison.lhs) ||
                expression_uses_signed_variable(comparison.rhs);
            if (signed_comparison) {
                emit_load_absolute(rhs_slot.value_hi_symbol);
                code.push_back(0x49);  // EOR #$80 normalizes signed order
                code.push_back(0x80);
                code.push_back(0x85);  // STA $02
                code.push_back(0x02);
                emit_load_absolute(lhs_slot.value_hi_symbol);
                code.push_back(0x49);  // EOR #$80
                code.push_back(0x80);
                code.push_back(0xC5);  // CMP $02
                code.push_back(0x02);
            } else {
                emit_load_absolute(lhs_slot.value_hi_symbol);
                emit_compare_absolute(rhs_slot.value_hi_symbol);
            }

            if (comparison.op == "=") {
                false_branches.push_back(emit_branch(0xD0));  // BNE
                emit_load_absolute(lhs_slot.value_lo_symbol);
                emit_compare_absolute(rhs_slot.value_lo_symbol);
                true_branches.push_back(emit_branch(0xF0));  // BEQ
            } else if (comparison.op == "<>") {
                true_branches.push_back(emit_branch(0xD0));  // BNE
                emit_load_absolute(lhs_slot.value_lo_symbol);
                emit_compare_absolute(rhs_slot.value_lo_symbol);
                true_branches.push_back(emit_branch(0xD0));  // BNE
            } else if (comparison.op == "<") {
                true_branches.push_back(emit_branch(0x90));  // BCC
                false_branches.push_back(emit_branch(0xD0));  // BNE
                emit_load_absolute(lhs_slot.value_lo_symbol);
                emit_compare_absolute(rhs_slot.value_lo_symbol);
                true_branches.push_back(emit_branch(0x90));  // BCC
            } else if (comparison.op == "<=") {
                true_branches.push_back(emit_branch(0x90));  // BCC
                false_branches.push_back(emit_branch(0xD0));  // BNE
                emit_load_absolute(lhs_slot.value_lo_symbol);
                emit_compare_absolute(rhs_slot.value_lo_symbol);
                true_branches.push_back(emit_branch(0x90));  // BCC
                true_branches.push_back(emit_branch(0xF0));  // BEQ
            } else if (comparison.op == ">") {
                false_branches.push_back(emit_branch(0x90));  // BCC
                true_branches.push_back(emit_branch(0xD0));  // BNE
                emit_load_absolute(lhs_slot.value_lo_symbol);
                emit_compare_absolute(rhs_slot.value_lo_symbol);
                false_branches.push_back(emit_branch(0x90));  // BCC
                true_branches.push_back(emit_branch(0xD0));  // BNE
            } else if (comparison.op == ">=") {
                false_branches.push_back(emit_branch(0x90));  // BCC
                true_branches.push_back(emit_branch(0xD0));  // BNE
                emit_load_absolute(lhs_slot.value_lo_symbol);
                emit_compare_absolute(rhs_slot.value_lo_symbol);
                false_branches.push_back(emit_branch(0x90));  // BCC
                true_branches.push_back(emit_branch(0xB0));  // BCS
            } else {
                throw ToolError("BAD CONDITION");
            }

            for (std::size_t operand : false_branches) {
                patch_branch_to_current(operand);
            }
            emit_jump(false_label);
            for (std::size_t operand : true_branches) {
                patch_branch_to_current(operand);
            }
        };
        for (const SourceOp& op : proc.ops) {
            if (code.size() > 0xFFFF) {
                throw ToolError("TARGET OBJECT TOO LARGE");
            }
            source_lines.push_back(ObjLineRecord{
                static_cast<std::uint16_t>(code.size()),
                op.line,
            });
            auto block_active = [&]() {
                return std::all_of(if_stack.begin(), if_stack.end(), [](const IfFrame& frame) {
                    return frame.runtime || frame.active;
                });
            };
            if ((pending_while || pending_for) && op.kind != SourceOp::Kind::Do) {
                if (pending_while) {
                    throw ToolError(
                        "WHILE REQUIRES DO LINE " + std::to_string(pending_while->second));
                }
                throw ToolError(
                    "FOR REQUIRES DO LINE " + std::to_string(pending_for->line));
            }
            if (op.kind == SourceOp::Kind::If) {
                const bool parent_active = block_active();
                IfFrame frame;
                frame.parent_active = parent_active;
                if (!parent_active) {
                    frame.active = false;
                } else if (expression_uses_any_variable(op.value)) {
                    frame.runtime = true;
                    frame.next_label = new_control_label("IF_NEXT");
                    frame.end_label = new_control_label("IF_END");
                    emit_condition_false_jump(op.value, frame.next_label);
                } else {
                    auto value = expression_looks_real(op.value)
                        ? try_eval_real_condition(op.value)
                        : try_eval_const_condition(op.value, constants);
                    if (!value) {
                        throw ToolError("BAD IF LINE " + std::to_string(op.line));
                    }
                    frame.active = *value;
                    frame.branch_taken = *value;
                }
                if_stack.push_back(std::move(frame));
                continue;
            }
            if (op.kind == SourceOp::Kind::ElseIf) {
                if (if_stack.empty() || if_stack.back().saw_else) {
                    throw ToolError("BAD ELSEIF LINE " + std::to_string(op.line));
                }
                IfFrame& frame = if_stack.back();
                if (frame.runtime) {
                    emit_jump(frame.end_label);
                    define_control_label(frame.next_label);
                    frame.next_label = new_control_label("IF_NEXT");
                    emit_condition_false_jump(op.value, frame.next_label);
                    frame.active = true;
                } else if (!frame.parent_active || frame.branch_taken) {
                    frame.active = false;
                } else if (expression_uses_any_variable(op.value)) {
                    frame.runtime = true;
                    frame.active = true;
                    frame.next_label = new_control_label("IF_NEXT");
                    frame.end_label = new_control_label("IF_END");
                    emit_condition_false_jump(op.value, frame.next_label);
                } else {
                    auto value = expression_looks_real(op.value)
                        ? try_eval_real_condition(op.value)
                        : try_eval_const_condition(op.value, constants);
                    if (!value) {
                        throw ToolError("BAD ELSEIF LINE " + std::to_string(op.line));
                    }
                    frame.active = *value;
                    frame.branch_taken = *value;
                }
                continue;
            }
            if (op.kind == SourceOp::Kind::Else) {
                if (if_stack.empty() || if_stack.back().saw_else) {
                    throw ToolError("BAD ELSE LINE " + std::to_string(op.line));
                }
                IfFrame& frame = if_stack.back();
                frame.saw_else = true;
                if (frame.runtime) {
                    emit_jump(frame.end_label);
                    define_control_label(frame.next_label);
                    frame.next_label.clear();
                    frame.active = true;
                } else {
                    frame.active = frame.parent_active && !frame.branch_taken;
                    frame.branch_taken = frame.parent_active;
                }
                continue;
            }
            if (op.kind == SourceOp::Kind::Fi) {
                if (if_stack.empty()) {
                    throw ToolError("BAD FI LINE " + std::to_string(op.line));
                }
                IfFrame frame = std::move(if_stack.back());
                if_stack.pop_back();
                if (frame.runtime) {
                    if (!frame.next_label.empty()) {
                        define_control_label(frame.next_label);
                    }
                    define_control_label(frame.end_label);
                }
                continue;
            }
            if (op.kind == SourceOp::Kind::For) {
                auto clause = for_clause_from_line(op.value);
                if (!clause) {
                    throw ToolError("BAD FOR LINE " + std::to_string(op.line));
                }
                PendingForState state;
                state.active = block_active();
                state.clause = std::move(*clause);
                state.line = op.line;
                if (state.active) {
                    auto counter = variables.find(upper_ascii(state.clause.counter));
                    if (counter == variables.end()) {
                        throw ToolError(
                            "UNKNOWN FOR COUNTER LINE " + std::to_string(op.line) + ": " +
                            state.clause.counter);
                    }
                    if (expression_uses_variable(state.clause.step)) {
                        throw ToolError(
                            "DYNAMIC FOR STEP LINE " + std::to_string(op.line));
                    }
                    auto step_value = try_eval_const_expr(state.clause.step, constants);
                    if (!step_value) {
                        throw ToolError("BAD FOR STEP LINE " + std::to_string(op.line));
                    }
                    if (*step_value == 0) {
                        throw ToolError("ZERO FOR STEP LINE " + std::to_string(op.line));
                    }
                    state.descending = *step_value < 0;
                    state.counter = counter->second;
                    const std::string hidden =
                        "__FOR_" + std::to_string(next_control_label++);
                    add_variable(hidden + "_FINAL", true);
                    add_variable(hidden + "_STEP", true);
                    state.final_value = variables.at(hidden + "_FINAL");
                    state.step = variables.at(hidden + "_STEP");
                }
                pending_for = std::move(state);
                continue;
            }
            if (op.kind == SourceOp::Kind::While) {
                pending_while = std::make_pair(op.value, op.line);
                continue;
            }
            if (op.kind == SourceOp::Kind::Do) {
                LoopFrame frame;
                frame.active = block_active();
                frame.has_precondition = pending_while.has_value() || pending_for.has_value();
                frame.if_depth = if_stack.size();
                if (frame.active) {
                    if (pending_for) {
                        emit_load_word(pending_for->clause.initial);
                        emit_store_variable(pending_for->counter);
                        emit_load_word(pending_for->clause.final_value);
                        emit_store_variable(pending_for->final_value);
                        emit_load_word(pending_for->clause.step);
                        emit_store_variable(pending_for->step);
                        constants.erase(upper_ascii(pending_for->counter.name));
                    }
                    frame.start_label = new_control_label("LOOP_START");
                    frame.end_label = new_control_label("LOOP_END");
                    define_control_label(frame.start_label);
                    if (pending_while) {
                        emit_condition_false_jump(pending_while->first, frame.end_label);
                    } else if (pending_for) {
                        emit_condition_false_jump(
                            pending_for->counter.name +
                                (pending_for->descending ? " >= " : " <= ") +
                                pending_for->final_value.name,
                            frame.end_label);
                        frame.for_loop = ForLoopState{
                            pending_for->counter,
                            pending_for->step,
                            pending_for->descending,
                        };
                    }
                }
                pending_while.reset();
                pending_for.reset();
                loop_stack.push_back(std::move(frame));
                continue;
            }
            if (op.kind == SourceOp::Kind::Until) {
                if (loop_stack.empty() || loop_stack.back().saw_until ||
                    loop_stack.back().has_precondition ||
                    loop_stack.back().if_depth != if_stack.size()) {
                    throw ToolError("BAD UNTIL LINE " + std::to_string(op.line));
                }
                LoopFrame& frame = loop_stack.back();
                frame.saw_until = true;
                if (frame.active) {
                    emit_condition_false_jump(op.value, frame.start_label);
                }
                continue;
            }
            if (op.kind == SourceOp::Kind::Od) {
                if (loop_stack.empty() || loop_stack.back().if_depth != if_stack.size()) {
                    throw ToolError("BAD OD LINE " + std::to_string(op.line));
                }
                LoopFrame frame = std::move(loop_stack.back());
                loop_stack.pop_back();
                if (frame.active) {
                    if (!frame.saw_until) {
                        if (frame.for_loop) {
                            emit_load_word(
                                frame.for_loop->counter.name + " + " +
                                frame.for_loop->step.name);
                            emit_store_variable(frame.for_loop->counter);
                        }
                        emit_jump(frame.start_label);
                    }
                    define_control_label(frame.end_label);
                }
                continue;
            }
            if (op.kind == SourceOp::Kind::Exit) {
                if (loop_stack.empty()) {
                    throw ToolError("EXIT OUTSIDE LOOP LINE " + std::to_string(op.line));
                }
                if (block_active() && loop_stack.back().active) {
                    emit_jump(loop_stack.back().end_label);
                }
                continue;
            }
            if (!block_active()) {
                continue;
            }
            if (op.kind == SourceOp::Kind::Return) {
                terminal_top_level_return =
                    &op == &proc.ops.back() && if_stack.empty() &&
                    loop_stack.empty() && !pending_while && !pending_for;
                if (!proc.return_type.empty()) {
                    const std::string return_type = upper_ascii(proc.return_type);
                    if (return_type == "REAL") {
                        auto function = function_returns.find(upper_ascii(proc.name));
                        if (function == function_returns.end() ||
                            !function->second.real) {
                            throw ToolError(
                                "BAD FUNC ABI " + upper_ascii(proc.name));
                        }
                        const RealSlot result = emit_real_expr(op.value);
                        emit_real_copy(result, *function->second.real);
                        emit_load_absolute(function->second.real->pointer_lo_symbol);
                        emit_load_index_absolute(
                            0xAE,
                            function->second.real->pointer_hi_symbol);
                    } else {
                        emit_load_word(op.value);
                        if (return_type == "BYTE") {
                            code.push_back(0xA2);  // LDX #0 for a BYTE result
                            code.push_back(0x00);
                        }
                    }
                }
                code.push_back(0x60);  // RTS
            } else if (op.kind == SourceOp::Kind::Print) {
                emit_text(op.value);
            } else if (op.kind == SourceOp::Kind::PrintString) {
                emit_action_string(op.value);
            } else if (op.kind == SourceOp::Kind::Declare) {
                const std::string declaration_type = upper_ascii(op.aux);
                if (declaration_type == "REAL") {
                    add_real_variable(
                        op.value,
                        op.mode,
                        op.expression,
                        op.line);
                } else if (declaration_type.size() > 8 &&
                           declaration_type.substr(declaration_type.size() - 8) ==
                               "_POINTER") {
                    const std::string element_type =
                        declaration_type.substr(0, declaration_type.size() - 8);
                    add_pointer_variable(
                        op.value,
                        element_type,
                        op.mode,
                        op.expression,
                        op.line);
                } else {
                    add_variable(
                        op.value,
                        declaration_type == "CARD" || declaration_type == "INT",
                        op.mode,
                        op.expression,
                        op.line,
                        declaration_type == "INT");
                }
            } else if (op.kind == SourceOp::Kind::ArrayDeclare) {
                add_array_variable(
                    op.value,
                    op.aux,
                    op.size_expression,
                    op.mode,
                    op.expression,
                    op.line);
            } else if (op.kind == SourceOp::Kind::ReuDeclare) {
                add_variable(op.value, false, "INITIAL", "255", op.line);
                emit_reu_allocation(variables.at(upper_ascii(op.value)), op.aux, op.line);
            } else if (op.kind == SourceOp::Kind::Assign) {
                const std::string target = upper_ascii(op.value);
                if (op.mode == "INDEX" || op.mode == "DEREFERENCE") {
                    const IndexedSlot* indexed = nullptr;
                    if (op.mode == "INDEX") {
                        auto found = arrays.find(target);
                        if (found == arrays.end()) {
                            throw ToolError(
                                "UNKNOWN ARRAY LINE " + std::to_string(op.line) +
                                ": " + target);
                        }
                        indexed = &found->second;
                    } else {
                        auto found = pointers.find(target);
                        if (found == pointers.end()) {
                            throw ToolError(
                                "UNKNOWN POINTER LINE " + std::to_string(op.line) +
                                ": " + target);
                        }
                        indexed = &found->second;
                    }
                    if (indexed->element_is_real()) {
                        const RealSlot value = emit_real_expr(op.aux);
                        if (op.mode == "INDEX") {
                            emit_prepare_indexed(*indexed, op.expression);
                        } else {
                            emit_prepare_pointer(*indexed);
                        }
                        emit_store_real_indirect(value);
                        continue;
                    }
                    ExprTempSlot value = allocate_expr_temp();
                    emit_load_word(op.aux);
                    emit_store_word(value);
                    if (op.mode == "INDEX") {
                        emit_prepare_indexed(*indexed, op.expression);
                    } else {
                        emit_prepare_pointer(*indexed);
                    }
                    emit_store_indirect(*indexed, value);
                    continue;
                }
                auto real_variable = real_variables.find(target);
                if (real_variable != real_variables.end()) {
                    const RealSlot value = emit_real_expr(op.aux);
                    emit_real_copy(value, real_variable->second);
                } else {
                    auto variable = variables.find(target);
                    if (variable == variables.end()) {
                        throw ToolError(
                            "UNKNOWN VAR LINE " + std::to_string(op.line) + ": " + op.value);
                    }
                    if (auto call = parse_call_expression(op.aux)) {
                        if (call->name == "INT") {
                            if (call->arguments.size() != 1) {
                                throw ToolError("BAD CALL INT");
                            }
                            const RealSlot source_value = emit_real_expr(call->arguments.front());
                            emit_set_real_pointer(source_value, 0x02);
                            emit_jsr_import("RT_F_TO_I");
                        } else {
                            emit_load_word(op.aux);
                        }
                    } else {
                        emit_load_word(op.aux);
                    }
                    emit_store_variable(variable->second);
                    if (expression_uses_variable(op.aux)) {
                        constants.erase(target);
                    } else if (auto value = try_eval_const_expr(op.aux, constants)) {
                        constants[target] = *value;
                    } else {
                        constants.erase(target);
                    }
                }
            } else if (op.kind == SourceOp::Kind::PrintInt) {
                if (expression_uses_variable(op.value)) {
                    emit_load_word(op.value);
                    emit_jsr_import("RT_PRINT_I");
                    emit_cr();
                } else {
                    emit_text(std::to_string(eval_const_expr(op.value, constants)));
                }
            } else if (op.kind == SourceOp::Kind::PrintIntCall) {
                emit_load_word(op.value);
                emit_jsr_import("RT_PRINT_I");
            } else if (op.kind == SourceOp::Kind::PrintReal) {
                const RealSlot value = emit_real_expr(op.value);
                emit_set_real_pointer(value, 0x02);
                emit_jsr_import("RT_PRINT_F");
                if (op.aux == "NEWLINE") {
                    emit_cr();
                }
            } else {
                ParsedCall parsed_call{op.value, split_call_arguments(op.aux)};
                if (upper_ascii(parsed_call.name) == "OVERLAYCALL") {
                    if (parsed_call.arguments.size() != 1) {
                        throw ToolError(
                            "BAD OVERLAY CALL LINE " + std::to_string(op.line));
                    }
                    const std::string target_text = trim(parsed_call.arguments.front());
                    if (target_text.empty() ||
                        target_text.find_first_not_of(
                            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_") !=
                            std::string::npos) {
                        throw ToolError(
                            "BAD OVERLAY CALL LINE " + std::to_string(op.line));
                    }
                    const std::string target = module_from_arg(target_text);
                    if (overlay_names.count(target) == 0) {
                        throw ToolError(
                            "UNKNOWN OVERLAY LINE " + std::to_string(op.line) + ": " +
                            target);
                    }
                    code.push_back(0x20);  // Program-owned overlay is a direct JSR.
                    const std::uint16_t operand_offset =
                        static_cast<std::uint16_t>(code.size());
                    code.push_back(0x00);
                    code.push_back(0x00);
                    add_reloc(operand_offset, target);
                    continue;
                }
                if (emit_builtin(parsed_call)) {
                    continue;
                }
                if (emit_local_routine_call(parsed_call)) {
                    continue;
                }
                if (!parsed_call.arguments.empty()) {
                    throw ToolError(
                        "UNSUPPORTED CALL ARGS LINE " + std::to_string(op.line) + ": " + op.value);
                }
                const std::string call = upper_ascii(op.value);
                code.push_back(0x20);  // JSR absolute
                const std::uint16_t operand_offset = static_cast<std::uint16_t>(code.size());
                code.push_back(0x00);
                code.push_back(0x00);
                ObjReloc reloc;
                reloc.offset = operand_offset;
                if (local_names.count(call) != 0) {
                    reloc.symbol = call;
                } else {
                    reloc.import = true;
                    reloc.import_index = add_import(call);
                }
                relocs.push_back(reloc);
            }
        }
        if (!if_stack.empty()) {
            throw ToolError("BAD IF");
        }
        if (pending_while) {
            throw ToolError(
                "WHILE REQUIRES DO LINE " + std::to_string(pending_while->second));
        }
        if (pending_for) {
            throw ToolError(
                "FOR REQUIRES DO LINE " + std::to_string(pending_for->line));
        }
        if (!loop_stack.empty()) {
            throw ToolError("BAD LOOP");
        }
        if (!terminal_top_level_return) {
            code.push_back(0x60);  // Fall-through RTS
        }
        const std::uint16_t proc_size = static_cast<std::uint16_t>(code.size() - proc_offset);
        exports.push_back(ObjExport{upper_ascii(proc.name), proc_offset, proc_size});
    }

    std::size_t final_data_size = 0;
    for (const VarSlot& slot : data_slots) {
        final_data_size += slot.is_card ? 2 : 1;
    }
    for (const RealSlot& slot : real_slots) {
        final_data_size += slot.absolute_address ? 2 : 6;
    }
    for (const ExprTempSlot& slot : expr_temp_slots) {
        (void)slot;
        final_data_size += 4;
    }
    for (const ArraySlot& slot : array_slots) {
        final_data_size += slot.initial_data.size() + 2;
    }
    final_data_size += address_constant_slots.size() * 2;
    if (code.size() > 0xFFFF ||
        final_data_size > 0xFFFF - code.size()) {
        throw ToolError("TARGET OBJECT TOO LARGE");
    }

    for (const VarSlot& slot : data_slots) {
        const std::uint16_t lo_offset = static_cast<std::uint16_t>(code.size());
        code.push_back(static_cast<std::uint8_t>(slot.initial_value & 0xFF));
        exports.push_back(ObjExport{
            slot.lo_symbol,
            lo_offset,
            static_cast<std::uint16_t>(slot.is_card ? 2 : 1),
        });
        if (slot.is_card) {
            const std::uint16_t hi_offset = static_cast<std::uint16_t>(code.size());
            code.push_back(static_cast<std::uint8_t>(slot.initial_value >> 8));
            exports.push_back(ObjExport{slot.hi_symbol, hi_offset, 1});
        }
    }

    for (const ArraySlot& slot : array_slots) {
        if (!slot.initial_data.empty()) {
            const std::uint16_t data_offset =
                static_cast<std::uint16_t>(code.size());
            code.insert(
                code.end(), slot.initial_data.begin(), slot.initial_data.end());
            exports.push_back(ObjExport{
                slot.data_symbol,
                data_offset,
                static_cast<std::uint16_t>(slot.initial_data.size()),
            });
        }

        const std::uint16_t pointer_offset =
            static_cast<std::uint16_t>(code.size());
        if (slot.absolute_data_address) {
            code.push_back(static_cast<std::uint8_t>(
                *slot.absolute_data_address & 0xFF));
            code.push_back(static_cast<std::uint8_t>(
                *slot.absolute_data_address >> 8));
        } else {
            code.push_back(0x00);
            code.push_back(0x00);
            if (!slot.initial_data.empty()) {
                add_reloc(pointer_offset, slot.data_symbol);
            }
        }
        exports.push_back(ObjExport{
            slot.indexed.pointer.lo_symbol,
            pointer_offset,
            2,
        });
        exports.push_back(ObjExport{
            slot.indexed.pointer.hi_symbol,
            static_cast<std::uint16_t>(pointer_offset + 1),
            1,
        });
    }

    for (const RealSlot& slot : real_slots) {
        if (slot.byte_symbols.size() != 4 || slot.initial_value.size() != 4) {
            throw ToolError("BAD REAL SLOT");
        }
        if (!slot.absolute_address) {
            for (std::size_t i = 0; i < 4; ++i) {
                const std::uint16_t offset = static_cast<std::uint16_t>(code.size());
                code.push_back(slot.initial_value[i]);
                exports.push_back(ObjExport{
                    slot.byte_symbols[i],
                    offset,
                    static_cast<std::uint16_t>(i == 0 ? 4 : 1),
                });
            }
        }

        const std::uint16_t pointer_offset = static_cast<std::uint16_t>(code.size());
        if (slot.absolute_address) {
            code.push_back(static_cast<std::uint8_t>(*slot.absolute_address & 0xFF));
            code.push_back(static_cast<std::uint8_t>(*slot.absolute_address >> 8));
        } else {
            code.push_back(0x00);
            code.push_back(0x00);
            add_reloc(pointer_offset, slot.byte_symbols.front());
        }
        exports.push_back(ObjExport{slot.pointer_lo_symbol, pointer_offset, 2});
        exports.push_back(ObjExport{
            slot.pointer_hi_symbol,
            static_cast<std::uint16_t>(pointer_offset + 1),
            1,
        });
    }

    for (const ExprTempSlot& slot : expr_temp_slots) {
        std::uint16_t offset = static_cast<std::uint16_t>(code.size());
        code.push_back(0x00);
        exports.push_back(ObjExport{slot.value_lo_symbol, offset, 2});
        offset = static_cast<std::uint16_t>(code.size());
        code.push_back(0x00);
        exports.push_back(ObjExport{slot.value_hi_symbol, offset, 1});

        offset = static_cast<std::uint16_t>(code.size());
        code.push_back(0x00);
        code.push_back(0x00);
        exports.push_back(ObjExport{slot.pointer_lo_symbol, offset, 2});
        exports.push_back(ObjExport{
            slot.pointer_hi_symbol,
            static_cast<std::uint16_t>(offset + 1),
            1,
        });
        add_reloc(offset, slot.value_lo_symbol);
    }

    for (const AddressConstantSlot& slot : address_constant_slots) {
        const std::uint16_t offset = static_cast<std::uint16_t>(code.size());
        code.push_back(0x00);
        code.push_back(0x00);
        exports.push_back(ObjExport{slot.lo_symbol, offset, 2});
        exports.push_back(ObjExport{
            slot.hi_symbol,
            static_cast<std::uint16_t>(offset + 1),
            1,
        });
        add_reloc(offset, slot.target_symbol);
    }

    auto main_export = std::find_if(
        exports.begin(), exports.end(), [](const ObjExport& export_record) {
            return export_record.name == "MAIN";
        });
    if (main_export == exports.end() || main_export->offset != 0) {
        throw ToolError("BAD OBJECT");
    }
    main_export->size = static_cast<std::uint16_t>(code.size());

    std::ostringstream out;
    out << "OBJ1\n";
    out << "f "
        << fs::relative(
               source_path(fs::current_path(), module),
               fs::current_path()).generic_string()
        << "\n";
    for (const ObjExport& export_record : exports) {
        out << "x " << export_record.name << " " << export_record.offset << " "
            << export_record.size << "\n";
    }
    for (const ObjExport& export_record : exports) {
        std::set<int> body_imports;
        const std::size_t start = export_record.offset;
        const std::size_t end = start + export_record.size;
        for (const ObjReloc& reloc : relocs) {
            const std::size_t reloc_start = reloc.offset;
            if (reloc.import && reloc_start >= start && reloc_start + 1 < end) {
                body_imports.insert(reloc.import_index);
            }
        }
        out << "b ";
        for (const int import_index : body_imports) {
            if (import_index < 0) {
                throw ToolError("BAD OBJECT");
            }
            out << "u" << object_import_code(
                static_cast<std::size_t>(import_index));
        }
        out << "M\n";
    }
    for (const std::string& symbol : imports) {
        out << "u " << symbol << "\n";
    }
    out << "m " << bytes_to_hex(code) << "\n";
    for (const ObjReloc& reloc : relocs) {
        if (reloc.import) {
            out << "r " << reloc.offset << " u"
                << object_import_code(static_cast<std::size_t>(reloc.import_index))
                << "\n";
        } else {
            out << "r " << reloc.offset << " x " << reloc.symbol << "\n";
        }
    }
    for (const ObjLineRecord& line : source_lines) {
        out << "l " << line.offset << " " << line.line << "\n";
    }

    write_text_file(object_path(fs::current_path(), module), out.str());
    std::cout << "ACTC OK\n";
    return 0;
}

std::vector<fs::path> object_search_directories(const fs::path& root) {
    std::vector<fs::path> search_dirs = {
        project_dir(root, "OBJ"),
        project_dir(root, "LIB"),
    };
    const fs::path parent = root.parent_path();
    if (!parent.empty() && parent != root) {
        search_dirs.push_back(project_dir(parent, "LIB"));
    }
    return search_dirs;
}

std::optional<std::size_t> object_export_index_for_symbol(
    const ObjectFile& object,
    std::string_view symbol) {
    const std::string wanted = upper_ascii(symbol);
    for (std::size_t i = 0; i < object.exports.size(); ++i) {
        if (object.exports[i].name == wanted) {
            return i;
        }
    }
    return std::nullopt;
}

fs::path find_object_for_symbol(const fs::path& root, const std::string& symbol) {
    const std::string wanted = upper_ascii(symbol);
    std::string filename_stem = wanted;
    std::replace(filename_stem.begin(), filename_stem.end(), '.', '_');
    const std::vector<fs::path> search_dirs = object_search_directories(root);
    for (const fs::path& dir : search_dirs) {
        auto found = child_case_insensitive(dir, wanted + ".OBJ");
        if (!found && filename_stem != wanted) {
            found = child_case_insensitive(dir, filename_stem + ".OBJ");
        }
        if (found && fs::is_regular_file(*found)) {
            const ObjectFile object = parse_object_file(*found);
            if (!object_export_index_for_symbol(object, wanted)) {
                throw ToolError("BAD OBJECT");
            }
            return *found;
        }
    }

    std::vector<fs::path> candidates;
    for (const fs::path& dir : search_dirs) {
        if (!fs::is_directory(dir)) {
            continue;
        }
        for (const fs::directory_entry& entry : fs::directory_iterator(dir)) {
            if (entry.is_regular_file() &&
                upper_ascii(entry.path().extension().string()) == ".OBJ") {
                candidates.push_back(entry.path());
            }
        }
    }
    std::sort(candidates.begin(), candidates.end(), [](const fs::path& lhs, const fs::path& rhs) {
        return upper_ascii(lhs.generic_string()) < upper_ascii(rhs.generic_string());
    });

    std::vector<fs::path> matches;
    std::set<std::string> seen_paths;
    for (const fs::path& candidate : candidates) {
        if (!seen_paths.insert(upper_ascii(candidate.lexically_normal().generic_string())).second) {
            continue;
        }
        try {
            const ObjectFile object = parse_object_file(candidate);
            if (object_export_index_for_symbol(object, wanted)) {
                matches.push_back(candidate);
            }
        } catch (const ToolError&) {
            // Unselected malformed or legacy objects are outside the closure.
        }
    }
    if (matches.size() > 1) {
        throw ToolError("DUPLICATE EXPORT " + wanted);
    }
    if (!matches.empty()) {
        return matches.front();
    }
    throw ToolError("UNRESOLVED " + wanted);
}

struct LinkedObjectSelection {
    ObjectFile object;
    fs::path path;
    std::size_t export_index = 0;
    std::uint16_t base = 0;
    std::vector<std::uint8_t> code;
};

const ObjExport& linked_selection_export(const LinkedObjectSelection& selection) {
    return selection.object.exports.at(selection.export_index);
}

std::size_t linked_selection_start(const LinkedObjectSelection& selection) {
    return linked_selection_export(selection).offset;
}

std::size_t linked_selection_end(const LinkedObjectSelection& selection) {
    const ObjExport& export_record = linked_selection_export(selection);
    return static_cast<std::size_t>(export_record.offset) + export_record.size;
}

bool linked_selection_contains_offset(
    const LinkedObjectSelection& selection,
    std::size_t offset) {
    return offset >= linked_selection_start(selection) &&
           offset < linked_selection_end(selection);
}

bool linked_selection_contains_reloc(
    const LinkedObjectSelection& selection,
    const ObjReloc& reloc) {
    const std::size_t offset = reloc.offset;
    return offset >= linked_selection_start(selection) &&
           offset + 1 < linked_selection_end(selection);
}

bool linked_selection_intersects_reloc(
    const LinkedObjectSelection& selection,
    const ObjReloc& reloc) {
    const std::size_t offset = reloc.offset;
    return offset < linked_selection_end(selection) &&
           offset + 2 > linked_selection_start(selection);
}

bool linked_selection_contains_export(
    const LinkedObjectSelection& selection,
    const ObjExport& export_record) {
    return linked_selection_contains_offset(selection, export_record.offset);
}

bool linked_selection_fully_contains_export(
    const LinkedObjectSelection& selection,
    const ObjExport& export_record) {
    const std::size_t start = export_record.offset;
    const std::size_t end = start + export_record.size;
    return start >= linked_selection_start(selection) &&
           end <= linked_selection_end(selection);
}

std::size_t object_selection_export_index_for_symbol(
    const ObjectFile& object,
    std::string_view symbol) {
    const auto requested = object_export_index_for_symbol(object, symbol);
    if (!requested) {
        throw ToolError("BAD OBJECT");
    }
    if (*requested < object.bodies.size()) {
        return *requested;
    }

    const ObjExport& requested_export = object.exports[*requested];
    std::optional<std::size_t> enclosing;
    for (std::size_t i = 0; i < object.bodies.size(); ++i) {
        const ObjExport& candidate = object.exports[i];
        const std::size_t candidate_end =
            static_cast<std::size_t>(candidate.offset) + candidate.size;
        const std::size_t requested_end =
            static_cast<std::size_t>(requested_export.offset) + requested_export.size;
        if (requested_export.offset < candidate.offset ||
            requested_end > candidate_end) {
            continue;
        }
        if (!enclosing || candidate.size < object.exports[*enclosing].size) {
            enclosing = i;
        }
    }
    if (!enclosing) {
        throw ToolError("BAD OBJECT");
    }
    return *enclosing;
}

std::string linked_selection_key(
    const fs::path& path,
    const ObjExport& export_record) {
    return upper_ascii(fs::absolute(path).lexically_normal().generic_string()) +
           "@" + std::to_string(export_record.offset) + ":" +
           std::to_string(export_record.size);
}

int cmd_alink(const std::vector<std::string>& args) {
    if (args.empty()) {
        throw ToolError("NO NAME");
    }
    const fs::path root = fs::current_path();
    const std::string module = module_from_arg(args.front());
    require_project_module(root, module);

    const std::string entry_symbol = "MAIN";
    std::vector<LinkedObjectSelection> selections;
    std::map<std::string, std::size_t> loaded_selections;
    std::map<std::string, std::pair<std::size_t, std::size_t>> exports;
    std::size_t cursor = 0;

    auto load_one = [&](const fs::path& path, const std::string& symbol) -> std::size_t {
        ObjectFile object = parse_object_file(path);
        const std::size_t export_index =
            object_selection_export_index_for_symbol(object, symbol);
        const ObjExport selected_export = object.exports[export_index];
        const std::string selection_key =
            linked_selection_key(path, selected_export);
        auto found = loaded_selections.find(selection_key);
        if (found != loaded_selections.end()) {
            return found->second;
        }

        LinkedObjectSelection selection;
        selection.object = std::move(object);
        selection.path = path;
        selection.export_index = export_index;
        const std::size_t start = selected_export.offset;
        const std::size_t end = start + selected_export.size;
        selection.code.assign(
            selection.object.code.begin() + static_cast<std::ptrdiff_t>(start),
            selection.object.code.begin() + static_cast<std::ptrdiff_t>(end));

        const std::size_t index = selections.size();
        loaded_selections[selection_key] = index;
        for (std::size_t i = 0; i < selection.object.exports.size(); ++i) {
            const ObjExport& export_record = selection.object.exports[i];
            if (!linked_selection_contains_export(selection, export_record)) {
                continue;
            }
            const std::string name = upper_ascii(export_record.name);
            if (exports.find(name) != exports.end()) {
                throw ToolError("DUPLICATE EXPORT " + name);
            }
            exports[name] = {index, i};
        }
        selections.push_back(std::move(selection));
        return index;
    };

    load_one(object_path(root, module), entry_symbol);
    while (cursor < selections.size()) {
        const LinkedObjectSelection& selection = selections[cursor];
        const ObjectFile& object = selection.object;
        std::vector<std::string> dependencies;
        for (const int import_index : object.bodies[selection.export_index].imports) {
            dependencies.push_back(
                object.imports[static_cast<std::size_t>(import_index)]);
        }
        for (const ObjReloc& reloc : object.relocs) {
            if (linked_selection_intersects_reloc(selection, reloc) &&
                !linked_selection_contains_reloc(selection, reloc)) {
                throw ToolError("BAD RELOC");
            }
            if (!linked_selection_contains_reloc(selection, reloc)) {
                continue;
            }
            if (reloc.import) {
                dependencies.push_back(
                    object.imports[static_cast<std::size_t>(reloc.import_index)]);
            } else {
                dependencies.push_back(reloc.symbol);
            }
        }
        ++cursor;
        for (const std::string& dependency : dependencies) {
            const std::string symbol = upper_ascii(dependency);
            if (exports.find(symbol) == exports.end()) {
                load_one(find_object_for_symbol(root, symbol), symbol);
            }
        }
    }

    const auto entry_export = exports.find(entry_symbol);
    if (entry_export == exports.end()) {
        throw ToolError("NO MAIN");
    }

    const std::uint16_t load_address = 0x1000;
    std::uint32_t address_cursor = load_address;
    for (LinkedObjectSelection& selection : selections) {
        selection.base = static_cast<std::uint16_t>(address_cursor);
        address_cursor += selection.code.size();
        if (address_cursor > 0x10000) {
            throw ToolError("PRG TOO LARGE");
        }
    }

    std::map<std::string, std::uint16_t> symbol_addresses;
    for (const auto& item : exports) {
        const LinkedObjectSelection& selection = selections[item.second.first];
        const ObjExport& export_record =
            selection.object.exports[item.second.second];
        symbol_addresses[item.first] = static_cast<std::uint16_t>(
            selection.base + export_record.offset - linked_selection_start(selection));
    }

    for (LinkedObjectSelection& selection : selections) {
        const ObjectFile& object = selection.object;
        for (const ObjReloc& reloc : object.relocs) {
            if (!linked_selection_contains_reloc(selection, reloc)) {
                continue;
            }
            std::string target;
            if (reloc.import) {
                if (reloc.import_index < 0 ||
                    static_cast<std::size_t>(reloc.import_index) >= object.imports.size()) {
                    throw ToolError("BAD OBJECT");
                }
                target = object.imports[static_cast<std::size_t>(reloc.import_index)];
            } else {
                target = reloc.symbol;
            }
            auto found = symbol_addresses.find(upper_ascii(target));
            if (found == symbol_addresses.end()) {
                throw ToolError("UNRESOLVED " + target);
            }
            const std::size_t patch_offset =
                static_cast<std::size_t>(reloc.offset) -
                linked_selection_start(selection);
            if (patch_offset + 1 >= selection.code.size()) {
                throw ToolError("BAD RELOC");
            }
            selection.code[patch_offset] =
                static_cast<std::uint8_t>(found->second & 0xFF);
            selection.code[patch_offset + 1] =
                static_cast<std::uint8_t>((found->second >> 8) & 0xFF);
        }
    }

    std::vector<std::uint8_t> prg;
    prg.push_back(static_cast<std::uint8_t>(load_address & 0xFF));
    prg.push_back(static_cast<std::uint8_t>((load_address >> 8) & 0xFF));
    for (const LinkedObjectSelection& selection : selections) {
        prg.insert(prg.end(), selection.code.begin(), selection.code.end());
    }
    write_binary_file(binary_path(root, module), prg);

    std::ostringstream dbg;
    dbg << "DBG1\n";
    dbg << "e " << symbol_addresses.at(entry_symbol) << "\n";
    for (std::size_t module_id = 0; module_id < selections.size(); ++module_id) {
        const LinkedObjectSelection& selection = selections[module_id];
        const ObjectFile& object = selection.object;
        const std::size_t selected_start = linked_selection_start(selection);
        dbg << "m " << module_id << " " << object.module << "\n";
        if (!object.source_file.empty()) {
            dbg << "f " << module_id << " " << object.source_file << "\n";
            for (const ObjLineRecord& line : object.lines) {
                if (!linked_selection_contains_offset(selection, line.offset)) {
                    continue;
                }
                dbg << "l "
                    << static_cast<std::uint16_t>(
                           selection.base + line.offset - selected_start)
                    << " " << module_id << " " << line.line << "\n";
            }
        }
        for (const ObjSourceFileRecord& file : object.source_files) {
            dbg << "f " << module_id << " " << file.id << " "
                << file.path << "\n";
        }
        for (const ObjProcRecord& procedure : object.procedures) {
            const ObjExport& symbol = object.exports[procedure.export_index];
            if (!linked_selection_contains_export(selection, symbol)) {
                continue;
            }
            dbg << "q " << module_id << " " << procedure.export_index << " "
                << static_cast<std::uint16_t>(
                       selection.base + symbol.offset - selected_start)
                << " " << procedure.file_id << " " << procedure.line << " "
                << procedure.column << " " << symbol.name << "\n";
        }
        for (const ObjNativeLineRecord& line : object.native_lines) {
            const ObjExport& symbol = object.exports[line.export_index];
            const std::size_t location =
                static_cast<std::size_t>(symbol.offset) + line.offset;
            if (!linked_selection_contains_offset(selection, location)) {
                continue;
            }
            dbg << "l " << module_id << " " << line.export_index << " "
                << static_cast<std::uint16_t>(
                       selection.base + location - selected_start)
                << " " << line.file_id << " " << line.line << " "
                << line.column << "\n";
        }

        auto data_export = std::find_if(
            object.exports.begin(), object.exports.end(),
            [](const ObjExport& symbol) {
                return symbol.name == "__IDATA";
            });
        if (data_export != object.exports.end() &&
            linked_selection_fully_contains_export(selection, *data_export) &&
            !object.variables.empty()) {
            std::vector<std::uint16_t> variable_offsets;
            std::uint32_t variable_cursor = 0;
            for (const ObjVariableMetadata& variable : object.variable_metadata) {
                if (variable_cursor + variable.width > data_export->size) {
                    throw ToolError("BAD OBJECT");
                }
                variable_offsets.push_back(
                    static_cast<std::uint16_t>(variable_cursor));
                variable_cursor += variable.width;
            }
            for (const ObjVariableRecord& variable : object.variables) {
                if (variable.scope != 'g' &&
                    !linked_selection_contains_export(
                        selection, object.exports[variable.export_index])) {
                    continue;
                }
                const ObjVariableMetadata& metadata =
                    object.variable_metadata[variable.variable_index];
                dbg << "v " << variable.scope << " " << variable.type << " "
                    << module_id << " ";
                if (variable.scope != 'g') {
                    dbg << variable.export_index << " ";
                }
                dbg << variable.variable_index << " "
                    << static_cast<std::uint16_t>(
                           selection.base + data_export->offset - selected_start +
                           variable_offsets[variable.variable_index])
                    << " " << metadata.width << " " << variable.file_id << " "
                    << variable.line << " " << variable.column << " "
                    << metadata.name << "\n";
            }
        }

        if (!object.source_file.empty() || !object.source_files.empty()) {
            for (const ObjExport& symbol : object.exports) {
                if (!linked_selection_fully_contains_export(selection, symbol)) {
                    continue;
                }
                dbg << "y "
                    << static_cast<std::uint16_t>(
                           selection.base + symbol.offset - selected_start)
                    << " " << symbol.size << " " << symbol.name << "\n";
            }
        }
    }
    write_text_file(debug_path(root, module), dbg.str());

    std::cout << "ALINK OK\n";
    return 0;
}

using CommandFn = int (*)(const std::vector<std::string>&);

std::optional<CommandFn> lookup_command(const std::string& command) {
    const std::string name = upper_ascii(command);
    if (name == "ACTNEW") return cmd_actnew;
    if (name == "ACTADD") return cmd_actadd;
    if (name == "ACTWORK") return cmd_actwork;
    if (name == "ACTSRC") return cmd_actsrc;
    if (name == "ACTFILE") return cmd_actfile;
    if (name == "ACTCHK") return cmd_actchk;
    if (name == "ACTDIR") return cmd_actdir;
    if (name == "ACTCOPY") return cmd_actcopy;
    if (name == "ACTDEL") return cmd_actdel;
    if (name == "ACTMKDIR") return cmd_actmkdir;
    if (name == "ACTRMDIR") return cmd_actrmdir;
    if (name == "ACTMOVE" || name == "ACTREN") return cmd_actmove;
    if (name == "ACTWRITE") return cmd_actwrite;
    if (name == "ACTINFO") return cmd_actinfo;
    if (name == "ACTMON") return cmd_actmon;
    if (name == "ACTDBG") return cmd_actdbg;
    if (name == "ACTTREE" || name == "TREE") return cmd_acttree;
    if (name == "XCOPY") return cmd_xcopy;
    if (name == "DELTREE") return cmd_deltree;
    if (name == "ACTEDIT") return cmd_actedit;
    if (name == "ACT2SAVE" || name == "ACTSAVE") return cmd_act2save;
    if (name == "ACTC") return cmd_actc;
    if (name == "ALINK") return cmd_alink;
    return std::nullopt;
}

std::string basename_without_extension(const char* argv0) {
    std::string base = fs::path(argv0).filename().string();
    const std::string suffix = ".exe";
    if (base.size() >= suffix.size() &&
        upper_ascii(std::string_view(base).substr(base.size() - suffix.size())) == upper_ascii(suffix)) {
        base.resize(base.size() - suffix.size());
    }
    return base;
}

void usage() {
    std::cerr
        << "usage: actnew <project>\n"
        << "       actadd <module>\n"
        << "       actwork\n"
        << "       actsrc\n"
        << "       actfile <module>\n"
        << "       actchk\n"
        << "       actdir [dir]\n"
        << "       actcopy <src> <dst>\n"
        << "       actdel <path>\n"
        << "       actmkdir <dir>\n"
        << "       actrmdir <dir>\n"
        << "       actmove <src> <dst>\n"
        << "       actwrite <path> [text...]\n"
        << "       actinfo\n"
        << "       actmon\n"
        << "       actdbg <module> [symbols|source|line|break|breaks|clear ...]\n"
        << "       acttree [dir]\n"
        << "       xcopy <src> <dst>\n"
        << "       deltree <path>\n"
        << "       actedit <module> [print|append|insert|replace|delete|index|find|symbols ...]\n"
        << "       act2save [module]\n"
        << "       actc <module>\n"
        << "       alink <module>\n";
}

}  // namespace

int main(int argc, char** argv) {
    std::string command = basename_without_extension(argv[0]);
    int first_arg = 1;
    auto fn = lookup_command(command);
    if (!fn && argc > 1) {
        command = argv[1];
        fn = lookup_command(command);
        first_arg = 2;
    }
    if (!fn) {
        usage();
        return 2;
    }

    std::vector<std::string> args;
    args.reserve(static_cast<std::size_t>(std::max(0, argc - first_arg)));
    for (int i = first_arg; i < argc; ++i) {
        args.emplace_back(argv[i]);
    }

    try {
        return (*fn)(args);
    } catch (const ToolError& err) {
        std::cerr << err.what() << "\n";
        return 1;
    } catch (const fs::filesystem_error& err) {
        std::cerr << err.what() << "\n";
        return 1;
    } catch (const std::exception& err) {
        std::cerr << "ERROR: " << err.what() << "\n";
        return 1;
    }
}
