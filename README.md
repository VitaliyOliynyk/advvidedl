# advvidedl

Pobiera wszystkie filmy z katalogu na vider.info (np. `https://vider.info/dir/+dse1v51`). Gdy vider.info pokaże captchę, odczytuje ją model DeepSeek. Jeśli to się nie uda, program prosi o wpisanie kodu w konsoli.

## Instalacja

Wymagany Python 3.11+ i [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Klucz DeepSeek

Wygeneruj klucz na https://platform.deepseek.com i ustaw go jako zmienną środowiskową:

```powershell
$env:DEEPSEEK_API_KEY = "sk-..."
```

albo skopiuj `.env.example` do `.env` w katalogu, z którego uruchamiasz program. Bez klucza captchę trzeba wpisać ręcznie.

## Użycie

```bash
uv run advvidedl <url_katalogu> [-o KATALOG] [--dry-run]
```

| Parametr | Opis |
|---|---|
| `<url_katalogu>` | Adres katalogu, np. `https://vider.info/dir/+dse1v51` |
| `-o`, `--output` | Katalog docelowy (domyślnie bieżący). Jeśli nie istnieje, zostanie utworzony |
| `--dry-run` | Tylko wypisuje listę filmów (ID, nazwa pliku, adres), nic nie pobiera |
| `--ai-attempts N` | Ile razy captchę rozwiązuje DeepSeek, zanim program poprosi o wpisanie kodu (domyślnie 4) |
| `--max-captcha N` | Maksymalna liczba podejść do captchy (domyślnie 12) |
| `--model` | Model DeepSeek z obsługą obrazów (domyślnie `deepseek-flash`, można też ustawić `DEEPSEEK_MODEL`) |

Przykład:

```bash
uv run advvidedl https://vider.info/dir/+dse1v51 -o "D:\Filmy\Pokemon S01"
```

- Pliki są nazywane według tytułów z katalogu (`<tytuł>.mp4`).
- Istniejące pliki są pomijane.
- Przerwane pobieranie (`<tytuł>.mp4.part`) jest wznawiane przy następnym uruchomieniu.
- Kod wyjścia `0` oznacza, że pobrano wszystko. `1` oznacza, że coś się nie udało (captcha, sieć albo któryś plik). `2` oznacza błędne argumenty.

## Jak to działa

- Captcha zabezpiecza tylko strony HTML, a pojawia się już po kilku zapytaniach z jednego IP. Program pobiera tylko jedną stronę: listę katalogu. Captchę rozwiązuje w pętli, bo potrafi wrócić 2–4 razy także po poprawnej odpowiedzi.
- Kod w linku `/vid/+f<kod>` to zakodowane ID pliku (podmienione cyfry: `m n x s e 8 1 5 c v` = `0–9`). Dzięki temu nie trzeba otwierać strony każdego filmu.
- Filmy są pobierane z `https://stream.vider.info/video/<id>/v.mp4`. Ten serwer nie jest chroniony captchą. To wersja do odtwarzania online, często mniejsza niż rozmiar oryginału podany na stronie.

## Testy

```bash
uv run pytest
```
