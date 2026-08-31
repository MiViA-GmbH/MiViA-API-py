# Changelog

## [0.4.1](https://github.com/MiViA-GmbH/MiViA-API-py/compare/mivia-v0.4.0...mivia-v0.4.1) (2026-08-31)


### Bug Fixes

* **client:** validate API key eagerly in SyncMiviaClient, matching MiviaClient ([700d566](https://github.com/MiViA-GmbH/MiViA-API-py/commit/700d566f4d9243b4a537941747d96d591cc8ac61))

## [0.4.0](https://github.com/MiViA-GmbH/MiViA-API-py/compare/mivia-v0.3.1...mivia-v0.4.0) (2026-08-31)


### ⚠ BREAKING CHANGES

* `image` is an object, results moved under `result`, and customization is `{config, template}`. `job.results` and `image_filename` stay available as properties. Adds get_jobs_status().

### Features

* add get_recent_job_ids method and recent-ids CLI command ([1abff4d](https://github.com/MiViA-GmbH/MiViA-API-py/commit/1abff4d7a0c5b90bd3a067a50a1273a6fcb06773))
* add list_all_jobs, enhance jobs list CLI with status filter and pagination ([bdeefc9](https://github.com/MiViA-GmbH/MiViA-API-py/commit/bdeefc9c0ea90216225ddbe8ac3634ac62dbfbb0))
* add proxy support via MIVIA_PROXY env var and --proxy CLI option ([898760d](https://github.com/MiViA-GmbH/MiViA-API-py/commit/898760d3fbecef6dbf6e850824f1c07457ddf45c))
* admin-only inline customization override on create_jobs ([3386abf](https://github.com/MiViA-GmbH/MiViA-API-py/commit/3386abfe0eb8002d3376b5276e9b07af6c0feffa))
* **client:** poll the async report endpoints ([d46b34e](https://github.com/MiViA-GmbH/MiViA-API-py/commit/d46b34e28feebc591594f829d43784a863d22bab))
* follow the reshaped jobs v2 response contract ([078bdfe](https://github.com/MiViA-GmbH/MiViA-API-py/commit/078bdfe96fce697899c3d864c85535045e68635a))
* initial commit ([362d736](https://github.com/MiViA-GmbH/MiViA-API-py/commit/362d7366937bd7464dfa5696018631f03df546ef))


### Bug Fixes

* add startedAt/finishedAt to JobDto, handle empty customization ([3e60dae](https://github.com/MiViA-GmbH/MiViA-API-py/commit/3e60dae4cbb14f1bbf96c404d8695b0035dac461))
* **client:** map 403 and 429 to typed errors ([15b3079](https://github.com/MiViA-GmbH/MiViA-API-py/commit/15b307999d797ae0d7ee40864644f75ed7aa0b70))
* **client:** parse plain array response from GET /jobs ([120806e](https://github.com/MiViA-GmbH/MiViA-API-py/commit/120806ec78ddd6e05fca4def36ad2ab9aa8bd5c1))
* **client:** report a cancelled report as such ([f4b5604](https://github.com/MiViA-GmbH/MiViA-API-py/commit/f4b5604eabff0e9d2b60ef6fc69bf4c1bc752c08))
* **client:** take the queued status and surface the in-flight cap ([b2dcb9d](https://github.com/MiViA-GmbH/MiViA-API-py/commit/b2dcb9d111f9bd9c354ac2417984c337bf513d1a))
* resolve ruff lint and format issues in CLI ([dc54cd5](https://github.com/MiViA-GmbH/MiViA-API-py/commit/dc54cd5510dfb02259b5f8910748d46b4ffe862c))


### Miscellaneous Chores

* restore release-please config ([0c0b1b5](https://github.com/MiViA-GmbH/MiViA-API-py/commit/0c0b1b596f0bab2ad228e19f617e496c1f4914cd))

## [0.1.3](https://github.com/MiViA-GmbH/MiViA-API-py/compare/mivia-v0.1.2...mivia-v0.1.3) (2026-01-29)


### Features

* add proxy support via MIVIA_PROXY env var and --proxy CLI option ([898760d](https://github.com/MiViA-GmbH/MiViA-API-py/commit/898760d3fbecef6dbf6e850824f1c07457ddf45c))
* initial commit ([362d736](https://github.com/MiViA-GmbH/MiViA-API-py/commit/362d7366937bd7464dfa5696018631f03df546ef))


### Bug Fixes

* resolve ruff lint and format issues in CLI ([dc54cd5](https://github.com/MiViA-GmbH/MiViA-API-py/commit/dc54cd5510dfb02259b5f8910748d46b4ffe862c))

## Changelog
