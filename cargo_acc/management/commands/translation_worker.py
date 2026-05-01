# cargo_acc/management/commands/translation_worker.py
import os
import time
from pathlib import Path

from autoi18n import Translator
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from cargodb.ui_i18n_keys import UI_TABLE_HEADER_KEYS


def get_target_langs() -> list[str]:
    """
    Берем список языков строго из настроек/окружения.
    Без догадок.
    """
    langs = getattr(settings, "AUTO_I18N_TARGET_LANGS", None)
    if langs:
        return [str(lang).strip() for lang in langs if str(lang).strip()]

    env_value = os.getenv("AUTO_I18N_TARGET_LANGS", "")
    if env_value.strip():
        return [item.strip() for item in env_value.split(",") if item.strip()]

    raise CommandError(
        "Не задан список языков перевода. "
        "Добавь AUTO_I18N_TARGET_LANGS в settings.py "
        "или переменную окружения AUTO_I18N_TARGET_LANGS=en,az,tr"
    )


def get_templates_dir() -> Path:
    templates_dir = Path(settings.BASE_DIR) / "web" / "templates"
    if not templates_dir.exists():
        raise CommandError(f"Папка шаблонов не найдена: {templates_dir}")
    return templates_dir


def iter_template_files(templates_dir: Path) -> list[Path]:
    return sorted(templates_dir.rglob("*.html"))


def build_page_name(template_path: Path, templates_dir: Path) -> str:
    rel_path = template_path.relative_to(templates_dir)
    return rel_path.with_suffix("").as_posix()


def make_file_html_getter(template_path: Path):
    def _getter() -> str:
        return template_path.read_text(encoding="utf-8")
    return _getter


def register_all_templates(
    translator: Translator,
    templates_dir: Path,
    target_langs: list[str],
) -> list[str]:
    registered_pages: list[str] = []

    for template_path in iter_template_files(templates_dir):
        page_name = build_page_name(template_path, templates_dir)

        translator.register_page(
            page_name=page_name,
            html_getter=make_file_html_getter(template_path),
            target_langs=target_langs,
        )
        registered_pages.append(page_name)

    return registered_pages


class Command(BaseCommand):
    help = "Run background translation worker loop"

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=300,
            help="Loop interval in seconds (default: 300)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Batch size for translation requests (default: 50)",
        )

    def handle(self, *args, **options):
        interval = options["interval"]
        batch_size = options["batch_size"]

        cache_dir = Path(settings.BASE_DIR) / "translations"
        cache_dir.mkdir(parents=True, exist_ok=True)

        templates_dir = get_templates_dir()
        target_langs = get_target_langs()

        self.stdout.write(
            self.style.SUCCESS(
                f"translation_worker started | interval={interval}s | "
                f"batch_size={batch_size} | target_langs={target_langs}"
            )
        )

        while True:
            try:
                translator = Translator(
                    cache_dir=str(cache_dir),
                    source_lang="ru",
                )

                registered_pages = register_all_templates(
                    translator=translator,
                    templates_dir=templates_dir,
                    target_langs=target_langs,
                )
                registered_keys = translator.register_keys(
                    items=UI_TABLE_HEADER_KEYS,
                    dict_name="system",
                    target_langs=target_langs,
                )

                self.stdout.write(
                    self.style.WARNING(
                        f"templates scanned: {len(registered_pages)}"
                    )
                )
                self.stdout.write(
                    self.style.WARNING(
                        f"ui keys registered: {registered_keys}"
                    )
                )
                for page_name in registered_pages:
                    self.stdout.write(f" - {page_name}")

                report = translator.process_all_translations(batch_size=batch_size)
                backend_report = translator.process_all_backend_key_translations(batch_size=batch_size)

                self.stdout.write(
                    self.style.SUCCESS(f"translation report: {report}")
                )
                self.stdout.write(
                    self.style.SUCCESS(f"backend key translation report: {backend_report}")
                )

            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("translation_worker stopped"))
                break
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"translation_worker error: {exc}"))

            time.sleep(interval)