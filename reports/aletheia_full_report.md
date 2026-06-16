# Aletheia Dataset Report

Generated automatically from the cleaned Aletheia Telegram dataset.

## Dataset Context

This dataset contains Telegram messages collected from Brazilian antivaccine channels and groups. Each row corresponds to one Telegram message. The data include identifiers, timestamps, message content, media metadata, forwarding information, and engagement metrics.

## Dataset Overview

| Metric                | Value               |
|:----------------------|:--------------------|
| Rows                  | 63495               |
| Columns               | 30                  |
| Duplicate message IDs | 0                   |
| Unique channels       | 118                 |
| Unique users          | 8729                |
| Date start            | 2020-03-01 11:38:28 |
| Date end              | 2025-06-10 12:27:25 |
| Total views           | 255688836.0         |
| Total forwards        | 1608551.0           |
| Total reactions       | 2385051             |

## Main Columns

| column             | description                                     |   missing |   missing_pct |   unique | dtype          |
|:-------------------|:------------------------------------------------|----------:|--------------:|---------:|:---------------|
| channel_id         | Anonymized identifier for the Telegram channel. |         0 |          0    |      118 | str            |
| message_id         | Unique identifier for each Telegram message.    |         0 |          0    |    63495 | str            |
| user_id            | Anonymized identifier of the message author.    |        21 |          0.03 |     8729 | str            |
| date_parsed        | Human-readable message timestamp.               |         0 |          0    |    62868 | datetime64[us] |
| time_bin           | Temporal bin used for aggregation.              |        22 |          0.03 |       64 | datetime64[us] |
| language           | Detected language.                              |         0 |          0    |       41 | str            |
| is_vaccine_related | Indicator for vaccine-related content.          |     22679 |         35.72 |        2 | float64        |
| media_type         | Type of media attached to the message.          |     33381 |         52.57 |       28 | str            |
| views              | Number of views.                                |     24214 |         38.14 |    10601 | float64        |
| n_forwards         | Number of forwards for this message.            |     24197 |         38.11 |      844 | float64        |
| reactions          | Number of reactions.                            |         0 |          0    |     1046 | int64          |
| text_content       | Text content of the Telegram message.           |     11383 |         17.93 |    49412 | str            |

## Missing Values

The table below summarizes missing values by column. High missingness is expected for optional fields such as media metadata, replies, edits, and forwarding information.

| column                  |   missing |   missing_pct | dtype          |
|:------------------------|----------:|--------------:|:---------------|
| media_description       |     58079 |    91.4702    | str            |
| forward_from_n_forwards |     55965 |    88.1408    | float64        |
| forward_from_views      |     55965 |    88.1408    | float64        |
| forward_from_reactions  |     55939 |    88.0999    | float64        |
| forward_from            |     54202 |    85.3642    | str            |
| reply_to                |     48676 |    76.6612    | str            |
| media_path              |     39917 |    62.8664    | str            |
| media_url               |     34182 |    53.8342    | str            |
| media_title             |     33892 |    53.3774    | str            |
| edit_date               |     33442 |    52.6687    | datetime64[us] |
| media_type              |     33381 |    52.5726    | str            |
| views                   |     24214 |    38.1353    | float64        |
| n_forwards              |     24197 |    38.1085    | float64        |
| is_vaccine_related      |     22679 |    35.7178    | float64        |
| text_clean              |     15679 |    24.6933    | str            |
| text_content            |     11383 |    17.9274    | str            |
| time_bin                |        22 |     0.0346484 | datetime64[us] |
| user_id                 |        21 |     0.0330735 | str            |
| language                |         0 |     0         | str            |
| channel_id              |         0 |     0         | str            |
| collected_date          |         0 |     0         | datetime64[us] |
| date                    |         0 |     0         | int64          |
| message_id              |         0 |     0         | str            |
| reactions               |         0 |     0         | int64          |
| date_parsed             |         0 |     0         | datetime64[us] |
| text_length             |         0 |     0         | int64          |
| word_count              |         0 |     0         | int64          |
| has_media               |         0 |     0         | bool           |
| is_reply                |         0 |     0         | bool           |
| is_forwarded            |         0 |     0         | bool           |

## Column Profile

| column                  | description                                     | dtype          |   missing |   missing_pct |   unique | top_value                                                                        |   top_count |
|:------------------------|:------------------------------------------------|:---------------|----------:|--------------:|---------:|:---------------------------------------------------------------------------------|------------:|
| channel_id              | Anonymized identifier for the Telegram channel. | str            |         0 |          0    |      118 | <CHANNEL_HASH:15b89df7bcd31a345556>                                              |        7115 |
| collected_date          | Timestamp when the message was collected.       | datetime64[us] |         0 |          0    |    55362 | 2025-02-20 17:23:42                                                              |          43 |
| date                    | Original timestamp in Unix milliseconds.        | int64          |         0 |          0    |    62868 | 1749084826000                                                                    |           5 |
| edit_date               | Timestamp of last edit, if available.           | datetime64[us] |     33442 |         52.67 |    28859 | 2021-09-14 07:05:40                                                              |          21 |
| forward_from            | Source channel or user of a forwarded message.  | str            |     54202 |         85.36 |     1414 | <CHANNEL_HASH:4a74a4ce9adbde9b9ccc>                                              |        1117 |
| forward_from_n_forwards | Forward count of original forwarded message.    | float64        |     55965 |         88.14 |      713 | 2.0                                                                              |         322 |
| forward_from_reactions  | Reaction count of original forwarded message.   | float64        |     55939 |         88.1  |      758 | 0.0                                                                              |        3854 |
| forward_from_views      | View count of original forwarded message.       | float64        |     55965 |         88.14 |     5280 | 312.0                                                                            |          10 |
| is_vaccine_related      | Indicator for vaccine-related content.          | float64        |     22679 |         35.72 |        2 | 0.0                                                                              |       35345 |
| language                | Detected language.                              | str            |         0 |          0    |       41 | Portuguese                                                                       |       32306 |
| media_description       | Description of attached media content.          | str            |     58079 |         91.47 |     4993 | Vocês podem assistir nossos documentários sobre estes temas no canal Alcyon Plêi |          49 |
| media_path              | Local path to media file.                       | str            |     39917 |         62.87 |    23578 | 27401c0ac3256345fb61/314.mp4                                                     |           1 |
| media_title             | Title of attached media content.                | str            |     33892 |         53.38 |    28529 | sticker.webp                                                                     |         134 |
| media_type              | Type of media attached to the message.          | str            |     33381 |         52.57 |       28 | image/jpeg                                                                       |       13512 |
| media_url               | External media URL.                             | str            |     34182 |         53.83 |    27547 | https://ift.tt/2PhfeRr                                                           |           6 |
| message_id              | Unique identifier for each Telegram message.    | str            |         0 |          0    |    63495 | <CHANNEL_HASH:27401c0ac3256345fb61>_357                                          |           1 |
| n_forwards              | Number of forwards for this message.            | float64        |     24197 |         38.11 |      844 | 0.0                                                                              |        5224 |
| reactions               | Number of reactions.                            | int64          |         0 |          0    |     1046 | 0                                                                                |       42704 |
| reply_to                | Identifier of the replied-to message.           | str            |     48676 |         76.66 |    13738 | <CHANNEL_HASH:3de2e13dcaec3cb5d3e2>_685224                                       |          12 |
| text_content            | Text content of the Telegram message.           | str            |     11383 |         17.93 |    49412 | https://t.me/<CHANNEL_HASH:5d56df3df06e8d09f32c> <ç<÷                            |         228 |
| user_id                 | Anonymized identifier of the message author.    | str            |        21 |          0.03 |     8729 | <USER_HASH:b09ba5f37e4104495d3c>                                                 |        2992 |
| views                   | Number of views.                                | float64        |     24214 |         38.14 |    10601 | 0.0                                                                              |         514 |
| date_parsed             | Human-readable message timestamp.               | datetime64[us] |         0 |          0    |    62868 | 2025-06-05 00:53:46                                                              |           5 |
| time_bin                | Temporal bin used for aggregation.              | datetime64[us] |        22 |          0.03 |       64 | 2020-06-01 00:00:00                                                              |        1000 |
| text_clean              |                                                 | str            |     15679 |         24.69 |    45386 | This community was blocked in Brazil following a decision of the Superior Electo |         218 |
| text_length             |                                                 | int64          |         0 |          0    |     2035 | 0                                                                                |       11383 |
| word_count              |                                                 | int64          |         0 |          0    |      583 | 0                                                                                |       11383 |
| has_media               |                                                 | bool           |         0 |          0    |        2 | False                                                                            |       33381 |
| is_reply                |                                                 | bool           |         0 |          0    |        2 | False                                                                            |       48676 |
| is_forwarded            |                                                 | bool           |         0 |          0    |        2 | False                                                                            |       54202 |

## Numeric Summary

| column                  |   count |            mean |              std |          min |           25% |            50% |            75% |             max |
|:------------------------|--------:|----------------:|-----------------:|-------------:|--------------:|---------------:|---------------:|----------------:|
| date                    |   63495 |     1.66712e+12 |      4.85709e+10 |  1.58306e+12 |   1.62497e+12 |    1.66719e+12 |    1.70912e+12 |     1.74956e+12 |
| views                   |   39281 |  6509.22        |  67928.4         |  0           | 507           | 1566           | 3776           |     1.1789e+07  |
| n_forwards              |   39298 |    40.9321      |    283.029       |  0           |   2           |    7           |   21           | 32637           |
| reactions               |   63495 |    37.5628      |    530.671       |  0           |   0           |    0           |    3           | 50820           |
| forward_from_n_forwards |    7530 |   135.234       |    833.044       |  0           |   6           |   18           |   65           | 37806           |
| forward_from_reactions  |    7556 |   289.059       |   2388.23        |  0           |   0           |    0           |   23           | 88569           |
| forward_from_views      |    7530 | 17536.6         | 151103           | 26           | 995.25        | 2909           | 8312.5         |     1.1789e+07  |

## Temporal Activity

![Messages over time](figures/full_report/messages_over_time.png)

## Language Distribution

![Language distribution](figures/full_report/language_distribution.png)

## Media Analysis

![Media type distribution](figures/full_report/media_types.png)

| media_type                              |   views_count |   views_mean |   views_median |   n_forwards_count |   n_forwards_mean |   n_forwards_median |   reactions_count |   reactions_mean |   reactions_median |
|:----------------------------------------|--------------:|-------------:|---------------:|-------------------:|------------------:|--------------------:|------------------:|-----------------:|-------------------:|
| image/jpeg                              |         12089 |    5847.57   |         1470   |              12094 |         29.2032   |                 6   |             13512 |         34.5474  |                0   |
| video/mp4                               |          9013 |    7018.08   |         1713   |               9019 |         61.4804   |                10   |             10099 |         56.2909  |                0   |
| webpage                                 |          3893 |    4370.38   |         1195   |               3894 |         28.7704   |                 4   |              5735 |         20.0045  |                0   |
| application/pdf                         |            99 |    7540.02   |         1161   |                 99 |        136.697    |                19   |               144 |          1.61806 |                0   |
| image/webp                              |            93 |    6409.6    |         6456   |                 93 |          2.32258  |                 1   |               209 |         26.622   |                1   |
| audio/ogg                               |            81 |    2593.33   |         1172   |                 81 |         28.8519   |                 5   |               136 |         25.9191  |                0   |
| poll                                    |            40 |    3826.85   |         1504   |                 40 |          4.475    |                 2   |                50 |         43.94    |                0   |
| audio/mpeg                              |            30 |    3309.6    |         1433.5 |                 30 |         28.1667   |                 5   |                50 |         13.46    |                0   |
| image/png                               |            28 |    1793.75   |           91   |                 28 |          1        |                 0   |                30 |          0       |                0   |
| video/quicktime                         |            22 |    6687.27   |          877   |                 22 |         67.5455   |                 9.5 |                24 |         88.4167  |                0.5 |
| audio/opus                              |            20 |    2270.15   |          338   |                 20 |         47.25     |                 2.5 |                48 |         16.7292  |                0   |
| audio/mp3                               |            11 |    3269.27   |         3404   |                 11 |         12.8182   |                11   |                15 |          1.06667 |                0   |
| audio/m4a                               |             6 |    3710.17   |         3492   |                  6 |         72.6667   |                71   |                22 |         34       |                0   |
| application/octet-stream                |             3 |      52.6667 |           52   |                  3 |          0.666667 |                 1   |                 4 |          0       |                0   |
| audio/x-opus+ogg                        |             3 |   13924.3    |        17364   |                  3 |         72        |                35   |                 6 |          2.5     |                0   |
| application/vnd.android.package-archive |             3 |      13.3333 |           15   |                  3 |          0        |                 0   |                 3 |          0       |                0   |
| audio/mp4                               |             3 |    3455      |         3409   |                  3 |         30.6667   |                45   |                 4 |          1.5     |                1   |
| application/epub+zip                    |             2 |     104      |          104   |                  2 |          3        |                 3   |                 3 |          0       |                0   |
| application/msword                      |             2 |     158.5    |          158.5 |                  2 |          5.5      |                 5.5 |                 2 |          0       |                0   |
| audio/aac                               |             2 |    2795.5    |         2795.5 |                  2 |         13.5      |                13.5 |                 3 |          0       |                0   |

## Channel Activity

![Top channels by message count](figures/full_report/top_channels.png)

| channel_id                          |   messages |        views_sum |   views_mean |   views_median |   n_forwards_sum |   n_forwards_mean |   n_forwards_median |   reactions_sum |   reactions_mean |   reactions_median |
|:------------------------------------|-----------:|-----------------:|-------------:|---------------:|-----------------:|------------------:|--------------------:|----------------:|-----------------:|-------------------:|
| <CHANNEL_HASH:15b89df7bcd31a345556> |       7115 |      9.75933e+06 |    17032     |         5394   |           140094 |         244.492   |                  20 |            2369 |       0.332959   |                0   |
| <CHANNEL_HASH:3de2e13dcaec3cb5d3e2> |       6829 |      2.64002e+06 |    11733.4   |         3281   |            18354 |          81.5733  |                  17 |            6073 |       0.889296   |                0   |
| <CHANNEL_HASH:b2d0f2a34116540fa51c> |       4414 |      6.54896e+06 |     3863.7   |          569   |            52521 |          30.9676  |                   6 |            7388 |       1.67377    |                0   |
| <CHANNEL_HASH:b09ba5f37e4104495d3c> |       2994 |      4.71129e+06 |     1574.63  |         1375.5 |            30817 |          10.2929  |                   6 |            3025 |       1.01035    |                0   |
| <CHANNEL_HASH:319ff846ea9101b66dfd> |       2942 |      5.76661e+06 |     1962.77  |         1777   |            36484 |          12.418   |                   7 |           41336 |      14.0503     |                1   |
| <CHANNEL_HASH:283ecc1042e9359269ad> |       2728 |      7.99993e+06 |     9852.13  |          738.5 |            28188 |          34.7143  |                   6 |            2269 |       0.831745   |                0   |
| <CHANNEL_HASH:279a22fc27f1d9171a59> |       2490 |      1.10584e+07 |     4442.91  |         4106   |            80112 |          32.1735  |                  18 |          216354 |      86.8892     |               86   |
| <CHANNEL_HASH:5d56df3df06e8d09f32c> |       2026 |      4.9236e+06  |     2561.71  |         2410   |            32755 |          17.0421  |                  10 |          104291 |      51.4763     |               47   |
| <CHANNEL_HASH:5e16f210a7dc1d2b7ff2> |       1878 |      2.094e+07   |    25289.8   |         3811   |           189169 |         228.189   |                  23 |              10 |       0.00532481 |                0   |
| <CHANNEL_HASH:f8dd7853d92b16ef9c28> |       1706 |      1.62729e+07 |    28300.6   |         3248   |            84548 |         147.04    |                  24 |               3 |       0.0017585  |                0   |
| <CHANNEL_HASH:751793d016c8dfbee9d1> |       1586 |      1.25143e+07 |     7900.43  |         8160.5 |            50429 |          31.8365  |                  15 |               0 |       0          |                0   |
| <CHANNEL_HASH:7d609299076727e5519a> |       1297 | 461751           |    17759.7   |         5826.5 |             8059 |         309.962   |                  46 |              21 |       0.0161912  |                0   |
| <CHANNEL_HASH:5c8f1dbc6fb1607fd67c> |       1194 |      1.12387e+06 |      942.843 |          905.5 |             4722 |           3.95809 |                   2 |            6661 |       5.57873    |                3   |
| <CHANNEL_HASH:ece83e9b700c7f9b2a6e> |       1157 |      1.65884e+06 |     1437.47  |         1330   |            11625 |          10.0737  |                   6 |           16780 |      14.503      |               10   |
| <CHANNEL_HASH:0eceb77fad5f8493ffb3> |       1112 |      7.78089e+06 |     7035.16  |         6868.5 |            62049 |          55.9504  |                  32 |          198034 |     178.088      |              150.5 |
| <CHANNEL_HASH:4a74a4ce9adbde9b9ccc> |       1091 | 930374           |      856.698 |          498.5 |            11404 |          10.5009  |                   5 |            7147 |       6.55087    |                2   |
| <CHANNEL_HASH:d91bf3e5a898cc055ad9> |       1058 |      1.53333e+06 |     1450.65  |         1090   |            15321 |          14.4948  |                   7 |            9027 |       8.53214    |                6   |
| <CHANNEL_HASH:59f557a48dd0bcf28cef> |       1056 | 991568           |      938.985 |          217.5 |            12321 |          11.6676  |                   1 |            1728 |       1.63636    |                0   |
| <CHANNEL_HASH:27401c0ac3256345fb61> |       1021 |      2.07504e+07 |    20688.3   |        22534   |            86228 |          85.9701  |                  53 |          304248 |     297.99       |                0   |
| <CHANNEL_HASH:254730b220c75b1ffdbb> |        993 |      3.85676e+06 |     3883.95  |         3735   |            22790 |          22.9507  |                  12 |           43735 |      44.0433     |               35   |

## Engagement Distributions

![Views distribution](figures/full_report/views_distribution.png)

![Forwards distribution](figures/full_report/forwards_distribution.png)

![Reactions distribution](figures/full_report/reactions_distribution.png)

## Text Length

![Text length distribution](figures/full_report/text_length_distribution.png)

![Word count distribution](figures/full_report/word_count_distribution.png)
