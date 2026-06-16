# Aletheia Portuguese Dataset Network Report

Generated automatically from the cleaned Portuguese Aletheia dataset.

## Dataset Context

This report focuses on the Portuguese subset of the Aletheia Telegram dataset. The selected data keep message identifiers, user identifiers, channel identifiers, message text, timestamps, reply links, forwarding metadata, and engagement metrics. The emphasis is on communication volume, channel/user activity, forwarding structure, reply structure, and engagement.

## Dataset Overview

| Metric                               | Value               |
|:-------------------------------------|:--------------------|
| Rows                                 | 32285               |
| Columns                              | 22                  |
| Duplicate message IDs                | 0                   |
| Unique channels                      | 109                 |
| Unique users                         | 5854                |
| Date start                           | 2020-03-01 11:38:28 |
| Date end                             | 2025-06-10 11:01:14 |
| Messages with replies                | 8315                |
| Messages forwarded from known source | 4947                |
| Known forward source channels        | 440                 |
| Known reply source channels          | 51                  |
| Total views                          | 123484688.0         |
| Total forwards                       | 640336.0            |
| Total reactions                      | 1606066             |
| Median text length                   | 155.0               |
| Median word count                    | 22.0                |

## Column Profile

| column                  | description                                                 | dtype          |   missing |   missing_pct |   unique | top_value                                                                                  |   top_count |
|:------------------------|:------------------------------------------------------------|:---------------|----------:|--------------:|---------:|:-------------------------------------------------------------------------------------------|------------:|
| message_id              | Unique anonymized Telegram message identifier.              | str            |         0 |          0    |    32285 | <CHANNEL_HASH:27401c0ac3256345fb61>_357                                                    |           1 |
| user_id                 | Anonymized identifier of the message author.                | str            |         0 |          0    |     5854 | <USER_HASH:319ff846ea9101b66dfd>                                                           |        1716 |
| channel_id              | Anonymized identifier of the Telegram channel.              | str            |         0 |          0    |      109 | <CHANNEL_HASH:3de2e13dcaec3cb5d3e2>                                                        |        5159 |
| text_content            | Portuguese text content of the message.                     | str            |         0 |          0    |    31781 | =¨Pessoal, estamos correndo contra o tempo para informar o maior número de pessoas possíve |          21 |
| text_clean              |                                                             | str            |         4 |          0.01 |    31696 | =¨Pessoal, estamos correndo contra o tempo para informar o maior número de pessoas possíve |          32 |
| date_parsed             | Human-readable message timestamp.                           | datetime64[us] |         0 |          0    |    32224 | 2023-01-15 23:32:51                                                                        |           3 |
| time_bin                | Time bin used for temporal aggregation.                     | datetime64[us] |         1 |          0    |       64 | 2022-02-01 00:00:00                                                                        |         707 |
| reply_to                | Message ID being replied to, when available.                | str            |     23970 |         74.25 |     7647 | <CHANNEL_HASH:3de2e13dcaec3cb5d3e2>_398741                                                 |           8 |
| forward_from            | Source channel/user of a forwarded message, when available. | str            |     27338 |         84.68 |      628 | <CHANNEL_HASH:4a74a4ce9adbde9b9ccc>                                                        |         771 |
| forward_from_n_forwards | Forward count of the original forwarded message.            | float64        |     28302 |         87.66 |      411 | 2.0                                                                                        |         189 |
| forward_from_reactions  | Reaction count of the original forwarded message.           | float64        |     28301 |         87.66 |      564 | 0.0                                                                                        |        1564 |
| forward_from_views      | View count of the original forwarded message.               | float64        |     28302 |         87.66 |     3053 | 359.0                                                                                      |           8 |
| n_forwards              | Number of forwards for the message.                         | float64        |     11501 |         35.62 |      477 | 0.0                                                                                        |        2668 |
| reactions               | Number of reactions for the message.                        | int64          |         0 |          0    |      751 | 0                                                                                          |       18039 |
| views                   | Number of views for the message.                            | float64        |     11502 |         35.63 |     7194 | 0.0                                                                                        |         306 |
| text_length             |                                                             | int64          |         0 |          0    |     1862 | 77                                                                                         |         152 |
| word_count              |                                                             | int64          |         0 |          0    |      562 | 12                                                                                         |         983 |
| is_reply                |                                                             | bool           |         0 |          0    |        2 | False                                                                                      |       23970 |
| is_forwarded            |                                                             | bool           |         0 |          0    |        2 | False                                                                                      |       27338 |
| reply_to_channel        |                                                             | string         |     23970 |         74.25 |       51 | <CHANNEL_HASH:3de2e13dcaec3cb5d3e2>                                                        |        4045 |
| forward_from_channel    |                                                             | string         |     27973 |         86.64 |      440 | <CHANNEL_HASH:4a74a4ce9adbde9b9ccc>                                                        |         771 |
| month                   |                                                             | str            |         0 |          0    |       64 | 2022-02                                                                                    |         706 |

## Missing Values

Missingness is expected in optional Telegram fields such as replies, forwarding metadata, and view counts.

| column                  |   missing |   missing_pct | dtype          |
|:------------------------|----------:|--------------:|:---------------|
| forward_from_views      |     28302 |   87.663      | float64        |
| forward_from_n_forwards |     28302 |   87.663      | float64        |
| forward_from_reactions  |     28301 |   87.6599     | float64        |
| forward_from_channel    |     27973 |   86.644      | string         |
| forward_from            |     27338 |   84.6771     | str            |
| reply_to                |     23970 |   74.245      | str            |
| reply_to_channel        |     23970 |   74.245      | string         |
| views                   |     11502 |   35.6265     | float64        |
| n_forwards              |     11501 |   35.6234     | float64        |
| text_clean              |         4 |    0.0123897  | str            |
| time_bin                |         1 |    0.00309741 | datetime64[us] |
| message_id              |         0 |    0          | str            |
| channel_id              |         0 |    0          | str            |
| user_id                 |         0 |    0          | str            |
| date_parsed             |         0 |    0          | datetime64[us] |
| text_content            |         0 |    0          | str            |
| reactions               |         0 |    0          | int64          |
| text_length             |         0 |    0          | int64          |
| is_reply                |         0 |    0          | bool           |
| word_count              |         0 |    0          | int64          |
| is_forwarded            |         0 |    0          | bool           |
| month                   |         0 |    0          | str            |

## Numeric Summary

| column                  |   count |       mean |       std |   min |   25% |   50% |    75% |             max |
|:------------------------|--------:|-----------:|----------:|------:|------:|------:|-------:|----------------:|
| forward_from_n_forwards |    3983 |    81.5119 |   383.717 |     0 |   6   |    17 |   56   |  9999           |
| forward_from_reactions  |    3984 |   369.978  |  2350.16  |     0 |   0   |     3 |   35   | 58668           |
| forward_from_views      |    3983 | 13813.5    | 51844.8   |    26 | 756.5 |  2348 | 6317.5 |     1.09526e+06 |
| n_forwards              |   20784 |    30.8091 |   161.225 |     0 |   2   |     7 |   21   |  9995           |
| reactions               |   32285 |    49.7465 |   711.626 |     0 |   0   |     0 |   10   | 50820           |
| views                   |   20783 |  5941.62   | 32223.5   |     0 | 490   |  1546 | 3453   |     1.1007e+06  |

## Temporal Activity

![Portuguese messages over time](figures/pt_report/messages_over_time.png)

## Network Overview

| metric                       |   value |
|:-----------------------------|--------:|
| Channel nodes                |     109 |
| User nodes                   |    5854 |
| User-channel edges           |    6337 |
| Forwarding edges             |    1052 |
| Reply edges                  |      51 |
| Messages with forward source |    4947 |
| Messages with replies        |    8315 |

## Channel Activity

![Top channels by message count](figures/pt_report/top_channels.png)

![Channel message volume vs unique users](figures/pt_report/channel_messages_vs_users.png)

![Channel message volume vs total views](figures/pt_report/channel_messages_vs_views.png)

### Top Channels

| channel_id                          |   messages |   unique_users |   replies |   forwarded_messages |      total_views |   mean_views |   median_views |   total_forwards |   mean_forwards |   total_reactions |   mean_reactions |   median_text_length |   reply_rate |   forwarded_rate |
|:------------------------------------|-----------:|---------------:|----------:|---------------------:|-----------------:|-------------:|---------------:|-----------------:|----------------:|------------------:|-----------------:|---------------------:|-------------:|-----------------:|
| <CHANNEL_HASH:3de2e13dcaec3cb5d3e2> |       5159 |           2869 |      4045 |                  240 |      1.58611e+06 |    14289.2   |         2554   |             6136 |       55.2793   |              5351 |       1.03722    |                 89   |   0.784067   |       0.0465206  |
| <CHANNEL_HASH:b2d0f2a34116540fa51c> |       2803 |            833 |      1367 |                 1013 |      4.29761e+06 |     3953.64  |          547   |            30153 |       27.7397   |              5405 |       1.92829    |                110   |   0.487692   |       0.361399   |
| <CHANNEL_HASH:319ff846ea9101b66dfd> |       1716 |              1 |       129 |                   63 |      3.5639e+06  |     2076.87  |         1833   |            24675 |       14.3794   |             30499 |      17.7733     |                154   |   0.0751748  |       0.0367133  |
| <CHANNEL_HASH:279a22fc27f1d9171a59> |       1530 |              1 |        20 |                   11 |      6.74774e+06 |     4410.28  |         4062   |            45878 |       29.9856   |            152784 |      99.8588     |                163   |   0.0130719  |       0.00718954 |
| <CHANNEL_HASH:283ecc1042e9359269ad> |       1480 |            459 |       486 |                  502 |      5.88236e+06 |    12383.9   |          710   |            18608 |       39.1747   |              1401 |       0.946622   |                113   |   0.328378   |       0.339189   |
| <CHANNEL_HASH:b09ba5f37e4104495d3c> |       1238 |              1 |        36 |                   95 |      2.14416e+06 |     1731.96  |         1491   |            16652 |       13.4507   |              2179 |       1.7601     |                207.5 |   0.0290792  |       0.0767367  |
| <CHANNEL_HASH:5d56df3df06e8d09f32c> |        997 |              1 |         0 |                   31 |      2.47743e+06 |     2484.88  |         2421   |            15603 |       15.6499   |             60382 |      60.5637     |                240   |   0          |       0.0310933  |
| <CHANNEL_HASH:f8dd7853d92b16ef9c28> |        948 |            383 |       394 |                  255 |      2.38827e+06 |     7171.99  |         3385   |            32025 |       96.1712   |                 1 |       0.00105485 |                121.5 |   0.415612   |       0.268987   |
| <CHANNEL_HASH:5e16f210a7dc1d2b7ff2> |        920 |            324 |       178 |                  356 |      1.26684e+07 |    34054.8   |         2915.5 |            85629 |      230.185    |                 8 |       0.00869565 |                159.5 |   0.193478   |       0.386957   |
| <CHANNEL_HASH:7d609299076727e5519a> |        865 |            578 |       617 |                   28 | 424402           |    23577.9   |         6787.5 |             7596 |      422        |                19 |       0.0219653  |                 76   |   0.713295   |       0.0323699  |
| <CHANNEL_HASH:ece83e9b700c7f9b2a6e> |        858 |              1 |        26 |                    1 |      1.23529e+06 |     1439.74  |         1337   |             9014 |       10.5058   |             15004 |      17.4872     |                196   |   0.030303   |       0.0011655  |
| <CHANNEL_HASH:5c8f1dbc6fb1607fd67c> |        810 |              1 |        64 |                  134 | 792244           |      978.079 |          952.5 |             3497 |        4.31728  |              5760 |       7.11111    |                144.5 |   0.0790123  |       0.165432   |
| <CHANNEL_HASH:254730b220c75b1ffdbb> |        798 |              1 |         0 |                   12 |      3.09683e+06 |     3880.74  |         3759   |            18688 |       23.4185   |             41046 |      51.4361     |                156   |   0          |       0.0150376  |
| <CHANNEL_HASH:95818eec6e27ddbade2b> |        689 |            314 |       403 |                   35 | 547626           |    15211.8   |         2409   |             7375 |      204.861    |               541 |       0.785196   |                 88   |   0.584906   |       0.0507983  |
| <CHANNEL_HASH:4a74a4ce9adbde9b9ccc> |        687 |              1 |        12 |                   35 | 600545           |      874.156 |          499   |             7826 |       11.3916   |              4964 |       7.22562    |                247   |   0.0174672  |       0.0509461  |
| <CHANNEL_HASH:59f557a48dd0bcf28cef> |        671 |              1 |         3 |                  112 | 644630           |      960.7   |          210   |             9202 |       13.7139   |               784 |       1.16841    |                221   |   0.00447094 |       0.166915   |
| <CHANNEL_HASH:0eceb77fad5f8493ffb3> |        665 |              1 |        10 |                  116 |      4.72918e+06 |     7111.56  |         6707   |            43717 |       65.7398   |            151009 |     227.081      |                310   |   0.0150376  |       0.174436   |
| <CHANNEL_HASH:27401c0ac3256345fb61> |        657 |              1 |        10 |                    2 |      1.36638e+07 |    20797.2   |        22534   |            52804 |       80.3714   |            235909 |     359.07       |                134   |   0.0152207  |       0.00304414 |
| <CHANNEL_HASH:54c716f77d71f87b00f6> |        532 |              1 |         8 |                    2 | 232650           |      437.312 |          291   |             1102 |        2.07143  |              3869 |       7.27256    |                205   |   0.0150376  |       0.0037594  |
| <CHANNEL_HASH:6412caddc25983e38597> |        525 |             77 |        33 |                  212 |      1.18495e+07 |    48365.4   |         7566   |            28537 |      116.478    |                19 |       0.0361905  |                198   |   0.0628571  |       0.40381    |
| <CHANNEL_HASH:5fc270120ab8dd2c2e0e> |        504 |             46 |        57 |                  253 | 871872           |     2690.96  |          938   |             7997 |       24.6821   |                43 |       0.0853175  |                175.5 |   0.113095   |       0.501984   |
| <CHANNEL_HASH:ae1c52aceb99bc1beee6> |        384 |              1 |         3 |                   20 |  43712           |      113.833 |          102   |              190 |        0.494792 |               382 |       0.994792   |                230.5 |   0.0078125  |       0.0520833  |
| <CHANNEL_HASH:da78cbfcdd42182acbb4> |        375 |              1 |         1 |                  138 | 156676           |      417.803 |          323   |             1343 |        3.58133  |               758 |       2.02133    |                177   |   0.00266667 |       0.368      |
| <CHANNEL_HASH:f610bd52ded770331f5b> |        343 |              1 |         0 |                  127 | 366400           |     1068.22  |          468   |             2467 |        7.19242  |              4982 |      14.5248     |                201   |   0          |       0.370262   |
| <CHANNEL_HASH:e16902a163770f460064> |        300 |              1 |         3 |                   10 | 391151           |     1303.84  |         1178   |             1313 |        4.37667  |              8385 |      27.95       |                714   |   0.01       |       0.0333333  |

## User Activity

![Top users by message count](figures/pt_report/top_users.png)

### Top Users

| user_id                          |   messages |   channels |   replies |   forwarded_messages |      total_views |   total_forwards |   total_reactions |   median_text_length |
|:---------------------------------|-----------:|-----------:|----------:|---------------------:|-----------------:|-----------------:|------------------:|---------------------:|
| <USER_HASH:319ff846ea9101b66dfd> |       1716 |          1 |       129 |                   63 |      3.5639e+06  |            24675 |             30499 |                154   |
| <USER_HASH:279a22fc27f1d9171a59> |       1530 |          1 |        20 |                   11 |      6.74774e+06 |            45878 |            152784 |                163   |
| <USER_HASH:4a74a4ce9adbde9b9ccc> |       1410 |          2 |        12 |                  731 |      1.31012e+06 |            18427 |              9496 |                260   |
| <USER_HASH:b09ba5f37e4104495d3c> |       1238 |          1 |        36 |                   95 |      2.14416e+06 |            16652 |              2179 |                207.5 |
| <USER_HASH:5d56df3df06e8d09f32c> |        997 |          1 |         0 |                   31 |      2.47743e+06 |            15603 |             60382 |                240   |
| <USER_HASH:ece83e9b700c7f9b2a6e> |        858 |          1 |        26 |                    1 |      1.23529e+06 |             9014 |             15004 |                196   |
| <USER_HASH:5c8f1dbc6fb1607fd67c> |        810 |          1 |        64 |                  134 | 792244           |             3497 |              5760 |                144.5 |
| <USER_HASH:254730b220c75b1ffdbb> |        798 |          1 |         0 |                   12 |      3.09683e+06 |            18688 |             41046 |                156   |
| <USER_HASH:da78cbfcdd42182acbb4> |        767 |          2 |         1 |                  519 |      5.45866e+06 |            14676 |              1830 |                188   |
| <USER_HASH:59f557a48dd0bcf28cef> |        679 |          2 |         3 |                  120 | 700982           |             9774 |               796 |                221   |
| <USER_HASH:0eceb77fad5f8493ffb3> |        665 |          1 |        10 |                  116 |      4.72918e+06 |            43717 |            151009 |                310   |
| <USER_HASH:27401c0ac3256345fb61> |        657 |          1 |        10 |                    2 |      1.36638e+07 |            52804 |            235909 |                134   |
| <USER_HASH:54c716f77d71f87b00f6> |        532 |          1 |         8 |                    2 | 232650           |             1102 |              3869 |                205   |
| <USER_HASH:a5a9bbff4cad23629770> |        385 |          1 |         3 |                  168 |      1.15748e+07 |            25212 |                19 |                229   |
| <USER_HASH:ae1c52aceb99bc1beee6> |        384 |          1 |         3 |                   20 |  43712           |              190 |               382 |                230.5 |
| <USER_HASH:f610bd52ded770331f5b> |        343 |          1 |         0 |                  127 | 366400           |             2467 |              4982 |                201   |
| <USER_HASH:e16902a163770f460064> |        300 |          1 |         3 |                   10 | 391151           |             1313 |              8385 |                714   |
| <USER_HASH:2e9e491df8d7008d8ba7> |        288 |          1 |         1 |                  203 |  27943           |              344 |               103 |                233.5 |
| <USER_HASH:42de3e0ebd704181202c> |        282 |          2 |         8 |                  207 | 475476           |             7019 |               271 |                141.5 |
| <USER_HASH:16a1103f30527bb3c9e6> |        280 |          1 |         0 |                    2 | 521348           |             3662 |             11620 |                233.5 |
| <USER_HASH:87c04c78445419c969f9> |        280 |          1 |         5 |                   10 | 748793           |             7303 |              7266 |                431.5 |
| <USER_HASH:59b50c953b0b10d3a20d> |        278 |          2 |         0 |                  125 | 952954           |            13543 |                 0 |                203.5 |
| <USER_HASH:7e8416c9abdd738a3a90> |        258 |          1 |         0 |                    1 | 494253           |             2812 |             21299 |                520   |
| <USER_HASH:f85c24dc51672d1ab8ae> |        241 |          1 |         5 |                  101 |  61163           |              691 |                16 |                211   |
| <USER_HASH:3de2e13dcaec3cb5d3e2> |        203 |          1 |        21 |                   70 |      1.28072e+06 |             3181 |               259 |                184   |

## User-Channel Network

Each user-channel edge represents posting activity by one user in one channel. The edge weight is the number of messages posted by that user in that channel.

![User-channel edge weight distribution](figures/pt_report/user_channel_edge_weights.png)

### Strongest User-Channel Edges

| user_id                          | channel_id                          |   messages |      total_views |   total_forwards |   total_reactions |
|:---------------------------------|:------------------------------------|-----------:|-----------------:|-----------------:|------------------:|
| <USER_HASH:319ff846ea9101b66dfd> | <CHANNEL_HASH:319ff846ea9101b66dfd> |       1716 |      3.5639e+06  |            24675 |             30499 |
| <USER_HASH:279a22fc27f1d9171a59> | <CHANNEL_HASH:279a22fc27f1d9171a59> |       1530 |      6.74774e+06 |            45878 |            152784 |
| <USER_HASH:b09ba5f37e4104495d3c> | <CHANNEL_HASH:b09ba5f37e4104495d3c> |       1238 |      2.14416e+06 |            16652 |              2179 |
| <USER_HASH:5d56df3df06e8d09f32c> | <CHANNEL_HASH:5d56df3df06e8d09f32c> |        997 |      2.47743e+06 |            15603 |             60382 |
| <USER_HASH:ece83e9b700c7f9b2a6e> | <CHANNEL_HASH:ece83e9b700c7f9b2a6e> |        858 |      1.23529e+06 |             9014 |             15004 |
| <USER_HASH:5c8f1dbc6fb1607fd67c> | <CHANNEL_HASH:5c8f1dbc6fb1607fd67c> |        810 | 792244           |             3497 |              5760 |
| <USER_HASH:254730b220c75b1ffdbb> | <CHANNEL_HASH:254730b220c75b1ffdbb> |        798 |      3.09683e+06 |            18688 |             41046 |
| <USER_HASH:4a74a4ce9adbde9b9ccc> | <CHANNEL_HASH:b2d0f2a34116540fa51c> |        723 | 709573           |            10601 |              4532 |
| <USER_HASH:4a74a4ce9adbde9b9ccc> | <CHANNEL_HASH:4a74a4ce9adbde9b9ccc> |        687 | 600545           |             7826 |              4964 |
| <USER_HASH:59f557a48dd0bcf28cef> | <CHANNEL_HASH:59f557a48dd0bcf28cef> |        671 | 644630           |             9202 |               784 |
| <USER_HASH:0eceb77fad5f8493ffb3> | <CHANNEL_HASH:0eceb77fad5f8493ffb3> |        665 |      4.72918e+06 |            43717 |            151009 |
| <USER_HASH:27401c0ac3256345fb61> | <CHANNEL_HASH:27401c0ac3256345fb61> |        657 |      1.36638e+07 |            52804 |            235909 |
| <USER_HASH:54c716f77d71f87b00f6> | <CHANNEL_HASH:54c716f77d71f87b00f6> |        532 | 232650           |             1102 |              3869 |
| <USER_HASH:da78cbfcdd42182acbb4> | <CHANNEL_HASH:283ecc1042e9359269ad> |        392 |      5.30198e+06 |            13333 |              1072 |
| <USER_HASH:a5a9bbff4cad23629770> | <CHANNEL_HASH:6412caddc25983e38597> |        385 |      1.15748e+07 |            25212 |                19 |
| <USER_HASH:ae1c52aceb99bc1beee6> | <CHANNEL_HASH:ae1c52aceb99bc1beee6> |        384 |  43712           |              190 |               382 |
| <USER_HASH:da78cbfcdd42182acbb4> | <CHANNEL_HASH:da78cbfcdd42182acbb4> |        375 | 156676           |             1343 |               758 |
| <USER_HASH:f610bd52ded770331f5b> | <CHANNEL_HASH:f610bd52ded770331f5b> |        343 | 366400           |             2467 |              4982 |
| <USER_HASH:e16902a163770f460064> | <CHANNEL_HASH:e16902a163770f460064> |        300 | 391151           |             1313 |              8385 |
| <USER_HASH:2e9e491df8d7008d8ba7> | <CHANNEL_HASH:2e9e491df8d7008d8ba7> |        288 |  27943           |              344 |               103 |
| <USER_HASH:87c04c78445419c969f9> | <CHANNEL_HASH:87c04c78445419c969f9> |        280 | 748793           |             7303 |              7266 |
| <USER_HASH:16a1103f30527bb3c9e6> | <CHANNEL_HASH:16a1103f30527bb3c9e6> |        280 | 521348           |             3662 |             11620 |
| <USER_HASH:7e8416c9abdd738a3a90> | <CHANNEL_HASH:7e8416c9abdd738a3a90> |        258 | 494253           |             2812 |             21299 |
| <USER_HASH:f85c24dc51672d1ab8ae> | <CHANNEL_HASH:f85c24dc51672d1ab8ae> |        241 |  61163           |              691 |                16 |
| <USER_HASH:3de2e13dcaec3cb5d3e2> | <CHANNEL_HASH:3de2e13dcaec3cb5d3e2> |        203 |      1.28072e+06 |             3181 |               259 |

## Forwarding Network

Forwarding edges are directed from the original forwarded source channel to the channel where the selected Portuguese message appears.

![Top forwarded-from source channels](figures/pt_report/top_forward_sources.png)

![Top forwarding edges](figures/pt_report/top_forward_edges.png)

### Top Forwarding Edges

| source_channel                      | target_channel                      |   messages |      total_views |   total_forwards |   total_reactions |
|:------------------------------------|:------------------------------------|-----------:|-----------------:|-----------------:|------------------:|
| <CHANNEL_HASH:4a74a4ce9adbde9b9ccc> | <CHANNEL_HASH:b2d0f2a34116540fa51c> |        668 | 561533           |             8007 |              4356 |
| <CHANNEL_HASH:da78cbfcdd42182acbb4> | <CHANNEL_HASH:283ecc1042e9359269ad> |        244 | 128502           |             1118 |               535 |
| <CHANNEL_HASH:42de3e0ebd704181202c> | <CHANNEL_HASH:d1ca5f3b123bd86a2bbb> |         82 | 337332           |             4872 |                99 |
| <CHANNEL_HASH:4a74a4ce9adbde9b9ccc> | <CHANNEL_HASH:2e9e491df8d7008d8ba7> |         68 |   5273           |               65 |                 8 |
| <CHANNEL_HASH:319ff846ea9101b66dfd> | <CHANNEL_HASH:5c8f1dbc6fb1607fd67c> |         64 |   8087           |               42 |                48 |
| <CHANNEL_HASH:6cce0c19c3cb3080103b> | <CHANNEL_HASH:1be3dcc814ab8a428aab> |         56 |   5132           |               51 |                 0 |
| <CHANNEL_HASH:319ff846ea9101b66dfd> | <CHANNEL_HASH:b09ba5f37e4104495d3c> |         53 |  58562           |              155 |                 0 |
| <CHANNEL_HASH:42de3e0ebd704181202c> | <CHANNEL_HASH:42de3e0ebd704181202c> |         46 |   3574           |               41 |                24 |
| <CHANNEL_HASH:319ff846ea9101b66dfd> | <CHANNEL_HASH:319ff846ea9101b66dfd> |         38 |  67451           |              485 |               127 |
| <CHANNEL_HASH:7b637e0dad023b0a9c41> | <CHANNEL_HASH:da78cbfcdd42182acbb4> |         37 |   6345           |               59 |                34 |
| <CHANNEL_HASH:0eceb77fad5f8493ffb3> | <CHANNEL_HASH:6412caddc25983e38597> |         36 | 272894           |             2008 |                 2 |
| <CHANNEL_HASH:b09ba5f37e4104495d3c> | <CHANNEL_HASH:b09ba5f37e4104495d3c> |         35 |  31880           |              324 |                26 |
| <CHANNEL_HASH:7b637e0dad023b0a9c41> | <CHANNEL_HASH:283ecc1042e9359269ad> |         35 | 612201           |             4414 |                30 |
| <CHANNEL_HASH:da78cbfcdd42182acbb4> | <CHANNEL_HASH:3de2e13dcaec3cb5d3e2> |         32 |  44862           |              538 |                 3 |
| <CHANNEL_HASH:54c716f77d71f87b00f6> | <CHANNEL_HASH:283ecc1042e9359269ad> |         31 |  50118           |              326 |                94 |
| <CHANNEL_HASH:71744f7659b8d983ad47> | <CHANNEL_HASH:6412caddc25983e38597> |         30 |      9.52457e+06 |            10232 |                 1 |
| <CHANNEL_HASH:f610bd52ded770331f5b> | <CHANNEL_HASH:283ecc1042e9359269ad> |         29 |  88099           |              475 |               178 |
| <CHANNEL_HASH:734777d57ab95a0e5328> | <CHANNEL_HASH:6412caddc25983e38597> |         28 |  65989           |              385 |                 2 |
| <CHANNEL_HASH:279a22fc27f1d9171a59> | <CHANNEL_HASH:f212c8a126befa4cf3bb> |         28 |  23891           |              155 |               755 |
| <CHANNEL_HASH:da78cbfcdd42182acbb4> | <CHANNEL_HASH:59f557a48dd0bcf28cef> |         28 |   7057           |               63 |                31 |
| <CHANNEL_HASH:f610bd52ded770331f5b> | <CHANNEL_HASH:da78cbfcdd42182acbb4> |         28 |   9452           |               84 |               115 |
| <CHANNEL_HASH:54c716f77d71f87b00f6> | <CHANNEL_HASH:f610bd52ded770331f5b> |         28 |  13824           |               64 |               271 |
| <CHANNEL_HASH:16a1103f30527bb3c9e6> | <CHANNEL_HASH:2e9e491df8d7008d8ba7> |         26 |   2944           |               20 |                 6 |
| <CHANNEL_HASH:da78cbfcdd42182acbb4> | <CHANNEL_HASH:f610bd52ded770331f5b> |         26 |   9442           |               80 |               258 |
| <CHANNEL_HASH:54c716f77d71f87b00f6> | <CHANNEL_HASH:da78cbfcdd42182acbb4> |         24 |   6039           |               48 |                60 |

## Reply Network

Reply edges are directed from the replied-to channel to the replying channel, when the replied-to message ID contains a recoverable channel hash.

![Top reply edges](figures/pt_report/top_reply_edges.png)

### Top Reply Edges

| source_channel                      | target_channel                      |   messages |   total_views |   total_forwards |   total_reactions |
|:------------------------------------|:------------------------------------|-----------:|--------------:|-----------------:|------------------:|
| <CHANNEL_HASH:3de2e13dcaec3cb5d3e2> | <CHANNEL_HASH:3de2e13dcaec3cb5d3e2> |       4045 |          4925 |               11 |              3377 |
| <CHANNEL_HASH:b2d0f2a34116540fa51c> | <CHANNEL_HASH:b2d0f2a34116540fa51c> |       1367 |           655 |               10 |               754 |
| <CHANNEL_HASH:7d609299076727e5519a> | <CHANNEL_HASH:7d609299076727e5519a> |        617 |             0 |                0 |                 4 |
| <CHANNEL_HASH:283ecc1042e9359269ad> | <CHANNEL_HASH:283ecc1042e9359269ad> |        486 |             0 |                0 |               170 |
| <CHANNEL_HASH:95818eec6e27ddbade2b> | <CHANNEL_HASH:95818eec6e27ddbade2b> |        403 |             0 |                0 |               327 |
| <CHANNEL_HASH:f8dd7853d92b16ef9c28> | <CHANNEL_HASH:f8dd7853d92b16ef9c28> |        394 |             0 |                0 |                 0 |
| <CHANNEL_HASH:5e16f210a7dc1d2b7ff2> | <CHANNEL_HASH:5e16f210a7dc1d2b7ff2> |        178 |           362 |               12 |                 0 |
| <CHANNEL_HASH:319ff846ea9101b66dfd> | <CHANNEL_HASH:319ff846ea9101b66dfd> |        129 |        316268 |             1950 |              1823 |
| <CHANNEL_HASH:ddf6b2a786902e6d8990> | <CHANNEL_HASH:ddf6b2a786902e6d8990> |        106 |             0 |                0 |                44 |
| <CHANNEL_HASH:a90cc9c390deeeabb031> | <CHANNEL_HASH:a90cc9c390deeeabb031> |         85 |             0 |                0 |                73 |
| <CHANNEL_HASH:5c8f1dbc6fb1607fd67c> | <CHANNEL_HASH:5c8f1dbc6fb1607fd67c> |         64 |         65129 |              208 |               436 |
| <CHANNEL_HASH:5fc270120ab8dd2c2e0e> | <CHANNEL_HASH:5fc270120ab8dd2c2e0e> |         57 |          2267 |               43 |                11 |
| <CHANNEL_HASH:d41e9a650622111f951e> | <CHANNEL_HASH:d41e9a650622111f951e> |         52 |             0 |                0 |                73 |
| <CHANNEL_HASH:126a2c585e5d0013453f> | <CHANNEL_HASH:126a2c585e5d0013453f> |         37 |         64192 |              303 |              1342 |
| <CHANNEL_HASH:b09ba5f37e4104495d3c> | <CHANNEL_HASH:b09ba5f37e4104495d3c> |         36 |         45579 |              255 |                 3 |
| <CHANNEL_HASH:6412caddc25983e38597> | <CHANNEL_HASH:6412caddc25983e38597> |         33 |          7742 |               11 |                 0 |
| <CHANNEL_HASH:d1ca5f3b123bd86a2bbb> | <CHANNEL_HASH:d1ca5f3b123bd86a2bbb> |         30 |             0 |                0 |                 9 |
| <CHANNEL_HASH:ece83e9b700c7f9b2a6e> | <CHANNEL_HASH:ece83e9b700c7f9b2a6e> |         26 |         35429 |              193 |               305 |
| <CHANNEL_HASH:279a22fc27f1d9171a59> | <CHANNEL_HASH:279a22fc27f1d9171a59> |         20 |        110361 |             1746 |              2053 |
| <CHANNEL_HASH:286732f26215f1f32de8> | <CHANNEL_HASH:286732f26215f1f32de8> |         19 |             0 |                0 |                10 |
| <CHANNEL_HASH:9c82030332b93b6fd512> | <CHANNEL_HASH:9c82030332b93b6fd512> |         12 |         34045 |              244 |              1209 |
| <CHANNEL_HASH:4a74a4ce9adbde9b9ccc> | <CHANNEL_HASH:4a74a4ce9adbde9b9ccc> |         12 |         10637 |              143 |               127 |
| <CHANNEL_HASH:0eceb77fad5f8493ffb3> | <CHANNEL_HASH:0eceb77fad5f8493ffb3> |         10 |         68306 |              222 |              1725 |
| <CHANNEL_HASH:15b89df7bcd31a345556> | <CHANNEL_HASH:15b89df7bcd31a345556> |         10 |             0 |                0 |                 0 |
| <CHANNEL_HASH:27401c0ac3256345fb61> | <CHANNEL_HASH:27401c0ac3256345fb61> |         10 |        284762 |              991 |              7861 |

## Engagement Distributions

![Views distribution](figures/pt_report/views_distribution.png)

![Forwards distribution](figures/pt_report/forwards_distribution.png)

![Reactions distribution](figures/pt_report/reactions_distribution.png)

## Text Length

![Text length distribution](figures/pt_report/text_length_distribution.png)

![Word count distribution](figures/pt_report/word_count_distribution.png)
