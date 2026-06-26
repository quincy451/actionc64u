# DBF1 Database Library

`LIB/DBF1.ACT` documents the current DBF helper names. ACTC recognizes these
names directly, emits imports for the helpers that are actually used, and ALINK
links only the referenced `RT_DBF_*.OBJ` modules into the final PRG.

Current scope:

- one staged DBF file at a time
- DBF images up to a 16-bit staged length
- header and current-record access, including delete-flag status/mutation, raw
  byte writes, and field-byte reads/writes from the staged DBF image
- creation of a new empty zero-field DBF image in the staged DBF slot
- append of one blank record to the staged DBF image
- pack of deleted records out of the staged DBF image
- explicit save-back of the staged DBF image to the staged filename
- handle `1` for a successfully opened or created file
- zero return values for inactive handles, invalid fields, invalid records, or
  failed file/REU operations

Helpers:

- `DbfCreate(filename)` stages a new empty zero-field DBF image using the
  supplied filename pointer and returns handle `1` on success. Use
  `DbfSave(handle)` to write it to disk.
- `DbfOpen(filename)` stages an existing DBF file and returns handle `1` on
  success.
- `DbfClose(handle)` clears the active DBF handle.
- `DbfGo(handle, recno)` moves to a one-based record number and returns success.
- `DbfFieldCount(handle)` returns the number of fields in the staged header.
- `DbfFieldLen(handle, field)` returns the length of a one-based field.
- `DbfReadByte(handle, offset)` returns a raw byte from the current record.
- `DbfReadFieldByte(handle, field, offset)` returns a byte from a one-based
  field and zero-based offset within that field.
- `DbfWriteFieldByte(handle, field, offset, value)` writes a byte to a
  one-based field and zero-based offset within that field, returning `1` on
  success.
- `DbfWriteByte(handle, offset, value)` writes one raw byte into the current
  record and returns `1` on success.
- `DbfAppend(handle)` appends one blank current record to the staged DBF image,
  increments the low 16-bit record count, makes the appended record current,
  and returns `1` on success. Use `DbfSave(handle)` to persist the append.
- `DbfPack(handle)` removes deleted records from the staged DBF image, preserves
  non-deleted records in order, updates the low 16-bit record count and current
  record, and returns `1` on success. Use `DbfSave(handle)` to persist the pack.
- `DbfSave(handle)` writes the staged DBF image back to the staged filename
  remembered by `DbfOpen` or `DbfCreate` and returns `1` on success.
- `DbfDelete(handle)` sets the current record's DBF delete flag to `*` and
  returns `1` on success.
- `DbfUndelete(handle)` clears the current record's DBF delete flag to space
  and returns `1` on success.
- `DbfDeleted(handle)` returns `1` when the current record's DBF delete flag is
  `*`, otherwise `0`.
- `DbfHeaderLen(handle)` returns the low byte of the staged DBF header length.
- `DbfRecordLen(handle)` returns the low byte of the staged DBF record length.
- `DbfTotalRecs(handle)` returns the low byte of the total record count.
- `DbfCurrRecNo(handle)` returns the low byte of the current record number.

Runtime modules:

- `RT_DBF_STATE.OBJ` stores linked DBF state.
- `RT_DBF_CREATE.OBJ` stages a new empty zero-field DBF image and initializes
  DBF state for the supplied filename.
- `RT_DBF_OPEN.OBJ` stages and parses the DBF header.
- `RT_DBF_CLOSE.OBJ` clears the active state.
- `RT_DBF_GO.OBJ` validates and updates the current record.
- `RT_DBF_FIELDCOUNT.OBJ` reads the field count from the header.
- `RT_DBF_FIELDLEN.OBJ` reads one field descriptor length.
- `RT_DBF_READBYTE.OBJ` reads one byte from the current record.
- `RT_DBF_READFIELDBYTE.OBJ` reads one field byte through
  `RT_DBF_FIELDLEN.OBJ` and `RT_DBF_READBYTE.OBJ`.
- `RT_DBF_WRITEFIELDBYTE.OBJ` writes one field byte through
  `RT_DBF_FIELDLEN.OBJ` and `RT_DBF_WRITEBYTE.OBJ`.
- `RT_DBF_WRITEBYTE.OBJ` writes one byte into the current record.
- `RT_DBF_APPEND.OBJ` appends one blank record in the staged DBF image and
  updates the staged record-count/header state.
- `RT_DBF_PACK.OBJ` compacts deleted records out of the staged DBF image and
  updates the staged record-count/header state.
- `RT_DBF_PACK_READ.OBJ`, `RT_DBF_PACK_WRITE.OBJ`,
  `RT_DBF_PACK_COPY.OBJ`, and `RT_DBF_PACK_STEP.OBJ` are transitive support
  modules used only when `RT_DBF_PACK.OBJ` is selected.
- `RT_DBF_SAVE.OBJ` writes the staged DBF image back through UDOS file-write
  services.
- `RT_DBF_DELETE.OBJ` marks the current record deleted through
  `RT_DBF_WRITEBYTE.OBJ`.
- `RT_DBF_UNDELETE.OBJ` clears the current record delete mark through
  `RT_DBF_WRITEBYTE.OBJ`.
- `RT_DBF_DELETED.OBJ` reads the current record delete flag through
  `RT_DBF_READBYTE.OBJ` and returns boolean status.
- `RT_DBF_HEADERLEN.OBJ` returns the staged DBF header-length low byte.
- `RT_DBF_RECORDLEN.OBJ` returns the staged DBF record-length low byte.
- `RT_DBF_TOTALRECS.OBJ` returns the staged record-count low byte.
- `RT_DBF_CURRRECNO.OBJ` returns the current-record low byte.

The DBF helpers are link-selected. Programs that do not call DBF functions do
not carry DBF helper code in the linked PRG.
