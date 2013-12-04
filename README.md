# MEMDAM (MEMory DAeMon)

## Goal

**Effortlessly** record **all** of your **personal** data in a **simple**, **secure** and **accessible** way to answer questions you care about.

- **Effortless**: No manual data entry required.
  This project is mostly concerned with data that can be collected automatically from other devices and services.
- **All**: It should be possible to use this project to collect any data you care about.
- **Personal**: This project is only concerned with Little Data--the kind of data that is related to a single person.
  If you want to record the price of every stock, or everyone's tweets, use something else.
- **Simple**: Nobody wants life to be complicated.
  Everything that happens to you in real life is an event, so all data is simply a collection of events.
- **Secure**: Only you have access to your data.
  Nothing is ever shared by default.
- **Accessible**: You have complete access to your data, and easy ways to answer the questions you care about.

## Status

If you are *not* a programmer, [email me](mailto:joshalbrecht@gmail.com) and let me know what you would like to use the project for.
I will notify you when it is ready.

If you *are* a programmer, see below for a description of the system, and [let me know](mailto:joshalbrecht@gmail.com) what you think of it.

The description below matches what is planned, not what already exists.
Now there is only a simple client and server.
Integrations with gmail, google hangouts, and google chat are currently in progress.
The next step is to have a simple demo for a single type of data (communications, eg, chats, emails, calls, texts, etc)

## Overview

Life is a series of events, so that is how we model it.

The only required information to create an [Event](https://github.com/joshalbrecht/memdam/) is a type (a [Namespace](https://github.com/joshalbrecht/memdam/)) and a time--all other fields are optional.
[Namespaces](https://github.com/joshalbrecht/memdam/) define the set of possible other fields that might be present on an event of that type.
See [the full schema for an Event](https://github.com/joshalbrecht/memdam/) for a description of how other fields are defined.

This system is simply responsible for two things:

1. **Recording [Events](https://github.com/joshalbrecht/memdam/).** There are three general ways that events can enter the system:
from a [historical import](https://github.com/joshalbrecht/memdam/) (ex: location history from Google Takeout),
from [synchronization with another service](https://github.com/joshalbrecht/memdam/) or device (ex: continually synching with Foursquare),
or from running a [special program](https://github.com/joshalbrecht/memdam/) on one or more devices that generates new events (ex: a special app that runs on your phone and records GPS data.)

2. **Finding and displaying [Events](https://github.com/joshalbrecht/memdam/)** to answer questions.
Through some combination of a REST API and a nice web interface, the goal is to make it possible to answer most questions about your data very easily.

There are two fundamentally different types of [Events](https://github.com/joshalbrecht/memdam/):

1. Discrete. These events happen at a particular time (like an email, text message, heart beats, adding a new friend on facebook, taking a picture, etc). Most of these types of events do not have numeric values and are better for displaying as text than graphing.
2. Continuous. These events are happening constantly, but you only sample them at a particular time (like location, body weight, heart rate, active window title, etc). Many of these types of events have numeric values and are great for graphing.

## Architecture

The system is divided into the following components:

### Archive

Responsible for storing all [Events](https://github.com/joshalbrecht/memdam/) in a secure, durable manner, and serving requests for those [Events](https://github.com/joshalbrecht/memdam/).

Because we take security so seriously,
and the only way to be sure that something is secure is to run it on hardware that you physically control,
the [Archive](https://github.com/joshalbrecht/memdam/) is designed to be easily installable and runnable from any environment that contains enough storage for your events.

This means that your archive either needs to be running constantly and be universally accessible,
or there needs to be a place to buffer events from [Collectors](https://github.com/joshalbrecht/memdam/) while the [Archive](https://github.com/joshalbrecht/memdam/) is offline.
For now we simply assume that the [Archive](https://github.com/joshalbrecht/memdam/) is always available.

Another possible future expansion is support for "virtual" sources.
Ex: instead of storing all events from Dropbox, simply acts as an interface that turns [Archive](https://github.com/joshalbrecht/memdam/) queries into queries to the Dropbox API, and then appropriately transforms the responses.

The current [Archive](https://github.com/joshalbrecht/memdam/) implementation uses [python](https://github.com/joshalbrecht/memdam/) and [sqlite](https://github.com/joshalbrecht/memdam/) for storage.
Each [Series](https://github.com/joshalbrecht/memdam/) (eg, all [Events](https://github.com/joshalbrecht/memdam/) with the same [Namespace](https://github.com/joshalbrecht/memdam/)) is stored in its own database file.
All databases are stored in the same folder (so that data can be easily encrypted, backed up, etc.)
If this seems weird, please read the [data storage architecture justification](https://github.com/joshalbrecht/memdam/), and after that, send me any questions or concerns that remain.

### Collectors

Responsible for writing [Events](https://github.com/joshalbrecht/memdam/) to the [Archive](https://github.com/joshalbrecht/memdam/).

[Collectors](https://github.com/joshalbrecht/memdam/) are *write-only* programs that generate [Events](https://github.com/joshalbrecht/memdam/) for a particular set of [Namespaces](https://github.com/joshalbrecht/memdam/) from some other device or service.
Generally, [Collectors](https://github.com/joshalbrecht/memdam/) should be grouped so that data that is requested/recorded together is within the same [Collector](https://github.com/joshalbrecht/memdam/).
There can be multiple instances of the same collector if you want different [Namespaces](https://github.com/joshalbrecht/memdam/) to be collected at different intervals (ex: if downloading from Google Takeout, you may wish to synchronize all of your youtube videos once per month because it is a lot of data, but synchronize your chats every day because it isn't much data)

There are four main types of [Collectors](https://github.com/joshalbrecht/memdam/):

1. **Historical**. These run once for a set of data, and then they are done.
2. **Samplers**. These run at a fixed interval, and query the current values of some external device or service. This current value is recorded. Note that data for one of these [Collectors](https://github.com/joshalbrecht/memdam/) is only recorded while the [Collector](https://github.com/joshalbrecht/memdam/) is running (however, they are much simpler to write). These are great for things like location, heart rate, mood, current window title, etc.
3. **Synchronizers**. These run at a fixed interval, and query the external device or service for its full state, then record any differences from the last run. These are more complicated to write because they must maintain some state about what [Events](https://github.com/joshalbrecht/memdam/) have already been recorded (typically a date of last synchronization, or a set of unique ids), but they can be very useful. These are great for things like email, facebook messages, flickr, other web services, etc.

### Displays

Responsible for displaying [Events](https://github.com/joshalbrecht/memdam/) in a way that makes it easy to answer particular questions.

This is currently the part of the system with the least design so far.

Tenatively, I think there are three main displays required:

1. **Timeline Display**. All Events should be able to be displayed in columns (or rows), sorted by date, and for convenient viewing.
This is at the very least required for debugging, and also would probably just look cool and be fun to play with.
2. **Search Display**. All Events should be searchable. Whether this search functionality is built on top of the Timeline View,
or whether the results come back in their own Display is still undecided.
3. **Widget Display**. This encompasses all other displays.
There will probably be generic widgets (ex: display the last X days of data from Y as a Z graph),
as well as more specialized widgets (ex: calculate a single number for today's "productivity score" based on a variety of data sources)

My current thought is that we will have a variety of displays, depending on which particular information you are interested in.
Examples include charts, lists of notifications, and other simple diplays for a dashboard.

There is also (I think) a need for a unified method of inspecting all data.
A sort of "time

## Event Data Model

## Namespaces

## Future:

There are plenty of interesting things to add in the future, including:

- Filters: transform or limit the information from a given collector.
Ex: if taking snapshots from a webcam, ignore any that have not changed very much.
Ex: if taking periodic screenshots, run some OCR on the resulting image to extract the visible text and store that as well.

- Triggers: check for a certain condition (ex: more than $X spent at restaurants in the past 30 days according to mint.com)
and perform a certain action (ex: send an email telling you to stop eating out so much)







#TODO: needs massive reorganization of stuff into a few different readmes

#general rule: prefer duplicate insertion of the same event where possible, since the insertion itself is idempotent and it should be exactly the same
#general rule: collectors often generate a wide variety of namespaces
#and should mostly be grouped by the actual collect (individual data can be turned on and off in the configuration)

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
