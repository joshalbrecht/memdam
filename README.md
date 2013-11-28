memdam
======

MEMory DA(e)Mon. A background process for archiving and serving all data about yourself.

all events have a namespace, according to this standard:
    datatype.device or datatype.service
    device data types are encourage to include a device_text_fts field (same for services)
    obviously this is for a single user, if there are multiple users then it becomes a UserEvent, and the namespace is understood to be userid.datatype.device, but that happens at a totally different future level
    instead of deviceOrService lets just call it source

how exactly to represent Events in memory?
    we want them to be simple and serializable and without any behavior
    but they also need to refer to files somehow (storing the entire thing in memory is too inefficient)
    choices:
            store everything related to the event in memory
                    bad because that's huge and broken
            store ONLY the data that is persisted
                    let's do this.
                    binaries are thus just stored in memory as UUIDs
                    to really use an event, you need to have some separate blobstore that allows you to read and write the binaries
                            can actually even use the same one on the client and server side
                            except that on the client side we always delete the data when finished sending, and on the server side they are NEVER deleted
                            note that the extension is NOT stored, so we are free to convert types, or even store redundant forms, etc
                                    will have to decide about this later
            store different things at different times
            give the event behavior that allows it to access the binary data


events are just json objects with a pretty flat structure
events are objects that have:
    required: sample_time: when the event was recorded. This value is valid between (sample_time - data_window_millis_int, sample_time] if data_window_size is defined
        This, being an integer, is the primary key because you cannot have two events at the same time, which is already stored for every row anyway as the rowid, so this is as efficient as possible
    optional: all other columns.
        If any are new when inserting, alter table to add the columns
        full specification of column names:
            all names are match: ([a-z_]*)_(int|float|binary|text|time|bool)(_(fts|asc|desc))*
            the first group is the name of the column
            the second group is the type of the column
                int: 8 byte integer
                float: 8 byte floating point number
                binary: stored as 16 bytes for a UUID. Events should represent this as a file path internally, with the name UUID.ext
                text: text, variable length, per SQLITE definition
                time: integer. will be stored as the number of milliseconds since UTC start. may be negative if the time is in the past
                bool: boolean. will be stored as an integer
            the third group is optional, and defines what indices to create:
                fts: a FTS4 index for text search. the type must be text
                asc: an ascending index.
                desc: a descending index. Should use this more often, since queries will likely be for more recent data than for super old data.
        examples of optional columns (these are pretty standard):
            (none): implies that this is a "counter" data type. Is recorded whenever we notice it happening, and that is it.
            value_text_fts: searchable text. may be further json for additional processing if you really want. can be large (a whole document). stored as ascii so that it can be lower case searched without changing the case of the data? Also often serves as a "string" version of "value"
            value_real: a numerical measurement
            value_int: special case of the above when this is always going to fit in a long
            data_window_millis_int: the period over which "value" was sampled. number of milliseconds.
            value_binary: special absolute file path (in code), UUID only in sql
        examples of less common possibilities:
            Imagine location: want to save two ints for mouse position: x_int and y_int
            or GPS location: lat_int  and long_int
            or semantic location: location_text_fts
            or postal location: street_text, state_text, zip_text, etc
            or a different searchable field: name_text_fts
