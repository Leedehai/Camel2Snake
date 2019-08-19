# Camel2Snake

A Python script to convert variable names in camelCase to snake_case using regular expression matching.

Usages:
```
./camel2snake.py --help
```

Sanity check examples:
```bash
./camel2snake.py --test "CookieData_t data2 = buildCookie(dataPieces, isHTTPOnly_, kDefaultOption);"
# result:
# CookieData_t data_2 = buildCookie(data_pieces, is_http_only_, kDefaultOption);

./camel2snake.py --test "bool bHasAnonymousUsers, authenticationNeeded, useHTTPSChannel;"
# result:
# bool has_anonymous_users, authentication_needed, use_https_channel;

./camel2snake.py --test "net::PacketBuffer *packetBuf = new net::PacketBuffer(memSize_);"
# result:
# net::PacketBuffer *packet_buffer = new net::PacketBuffer(memory_size_);
```

#### Prerequisites
macOS or Linux (Windows should be fine, but not tested)<br>
Python2.7+ or Python 3.4+

#### Motivation
Originally I'm used to using camelCase to name variables in C++. But as I work on the [Chromium](https://cs.chromium.org) project I start to appreciate snake_case, for no obvious reason. As a result, I decided to write a script to convert my other projects.

#### Limitation
Because the conversion is done using regex, there might be errors caused by lack of syntax awareness (see [camel2snake.py](camel2snake.py)'s comments at the top). A more precise approach is using Clang's Python bindings [cindex](https://github.com/llvm-mirror/clang/blob/master/bindings/python/clang/cindex.py).<br>
You may check [ccindex](https://github.com/Leedehai/ccindex) to see how cindex could be used to parse and extract info from C++ files. 

###### EOF
