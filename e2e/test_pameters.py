from typing import Callable, Dict
from e2e.fixures import (
    run_podcast_downloader,
    # fixures:
    use_config,
)


def test_parameter_config_file(
    use_config: Callable[[Dict], None],
):
    use_config({"podcasts": [{}]})

    # Act
    runner = run_podcast_downloader(["--config", "a.json"])

    # Assert
    assert runner.is_correct()
