# advvidedl

Pobiera filmy z vider.info: cały katalog (np. `https://vider.info/dir/+dse1v51`), zakres filmów z katalogu albo jeden film (np. `https://vider.info/vid/+fxn8m5x`). Gdy vider.info pokaże captchę, odczytuje ją model DeepSeek (`deepseek-flash`). Jeśli to się nie uda, program prosi o wpisanie kodu w konsoli. Działa na Windows i Linux, także w Dockerze.

## Instalacja

Wymagany Python 3.11+ i [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Klucz DeepSeek

Wygeneruj klucz na https://platform.deepseek.com i ustaw go jako zmienną środowiskową:

```powershell
$env:DEEPSEEK_API_KEY = "sk-..."      # PowerShell
```
```bash
export DEEPSEEK_API_KEY="sk-..."      # bash
```

albo skopiuj `.env.example` do `.env` w katalogu, z którego uruchamiasz program, i wpisz tam klucz. Bez klucza captchę trzeba wpisać ręcznie.

## Tryby pracy

Tryb wynika z podanego adresu:

| Adres | Tryb |
|---|---|
| `https://vider.info/dir/+d…` | **katalog**: wszystkie filmy albo zakres `--start` … `--end` |
| `https://vider.info/vid/+f…` | **film**: jeden film |
| brak adresu | **interaktywny**: program pyta o brakujące parametry |

Działają też adresy `vider.pl` oraz z `www.`.

## Parametry

```
advvidedl [URL] [-s FILM] [-e FILM] [-o KATALOG] [--dry-run]
          [--ai-attempts N] [--max-captcha N] [--model MODEL] [-h]
```

| Parametr | Opis |
|---|---|
| `URL` | Adres katalogu albo filmu. Bez niego program działa w trybie interaktywnym |
| `-s`, `--start FILM` | Pierwszy film do pobrania (tylko w trybie katalogu). Domyślnie pierwszy w katalogu |
| `-e`, `--end FILM` | Ostatni film do pobrania, włącznie (tylko w trybie katalogu). Domyślnie ostatni w katalogu |
| `-o`, `--output KATALOG` | Katalog docelowy (domyślnie bieżący). Jeśli nie istnieje, zostanie utworzony |
| `--dry-run` | Tylko wypisuje listę filmów (ID, nazwa pliku, adres), nic nie pobiera |
| `--ai-attempts N` | Ile razy captchę rozwiązuje DeepSeek, zanim program poprosi o wpisanie kodu (domyślnie 4) |
| `--max-captcha N` | Maksymalna liczba podejść do captchy na jedną stronę (domyślnie 12) |
| `--model MODEL` | Model DeepSeek z obsługą obrazów (domyślnie `deepseek-flash`, można też ustawić `DEEPSEEK_MODEL`) |
| `-h`, `--help` | Pokazuje pomoc z opisem parametrów i przykładami |

**`FILM`** w `--start` i `--end` można podać jako:
- **adres filmu**, np. `https://vider.info/vid/+fxn8xmn` (skopiowany z przeglądarki). Film musi należeć do podanego katalogu,
- **nazwę**: cały tytuł albo jego fragment, np. `"League 05"`. Wielkość liter nie ma znaczenia, a końcówkę `.mp4` program pomija. Jeśli fragment pasuje do kilku filmów, program je wypisze i poprosi o dokładniejszą nazwę. Nazwy ze spacjami trzeba ująć w cudzysłowy.

Reguły zakresu:
- bez `--start` i `--end` pobierany jest cały katalog,
- samo `--start` pobiera od tego filmu do końca katalogu,
- samo `--end` pobiera od początku katalogu do tego filmu,
- `--start` i `--end` razem pobierają oba filmy i wszystko pomiędzy (w kolejności z katalogu).

## Przykłady

W przykładach jest `uv run advvidedl` (z katalogu projektu). Zamiast tego można użyć `uv run python -m advvidedl`, a po instalacji pakietu (`pip install .`) samego `advvidedl`.

Cały katalog do bieżącego katalogu:
```bash
uv run advvidedl https://vider.info/dir/+dse1v51
```

Cały katalog do wskazanego katalogu (jeśli nie istnieje, zostanie utworzony):
```bash
uv run advvidedl https://vider.info/dir/+dse1v51 -o "D:\Filmy\Pokemon S01"
uv run advvidedl https://vider.info/dir/+dse1v51 -o ~/filmy/pokemon
```

Od filmu o podanej nazwie do końca katalogu:
```bash
uv run advvidedl https://vider.info/dir/+dse1v51 --start "League 05"
uv run advvidedl https://vider.info/dir/+dse1v51 -s "Spotkanie w Marmorii"
```

Od filmu o podanym adresie do końca katalogu:
```bash
uv run advvidedl https://vider.info/dir/+dse1v51 --start https://vider.info/vid/+fxn8xmn
```

Od filmu do filmu (włącznie), nazwami albo adresami, można też mieszać:
```bash
uv run advvidedl https://vider.info/dir/+dse1v51 -s "League 05" -e "League 07"
uv run advvidedl https://vider.info/dir/+dse1v51 -s https://vider.info/vid/+fxn8xmn -e "League 07"
```

Od początku katalogu do wskazanego filmu:
```bash
uv run advvidedl https://vider.info/dir/+dse1v51 --end "League 10"
```

Najpierw sprawdzenie, co zostanie pobrane (nic się nie pobiera):
```bash
uv run advvidedl https://vider.info/dir/+dse1v51 -s "League 05" -e "League 07" --dry-run
```
```
215201	Pokemon Indigo League 05- Spotkanie w Marmorii.mp4	https://stream.vider.info/video/215201/v.mp4?uid=0
215198	Pokemon Indigo League 06- Clefairy i kamień księżycowy.mp4	https://stream.vider.info/video/215198/v.mp4?uid=0
215203	Pokemon Indigo League 07- Wodne kwiaty Azurii.mp4	https://stream.vider.info/video/215203/v.mp4?uid=0
```

Jeden film:
```bash
uv run advvidedl https://vider.info/vid/+fxn8m5x
uv run advvidedl https://vider.info/vid/+fxn8m5x -o filmy
```

Bez DeepSeek, czyli captcha zawsze wpisywana ręcznie:
```bash
uv run advvidedl https://vider.info/dir/+dse1v51 --ai-attempts 0
```

Pomoc:
```bash
uv run advvidedl --help
```

### Tryb interaktywny

Uruchom program bez adresu. Zapyta tylko o to, czego nie podano w wierszu poleceń:

```
> uv run advvidedl
Podaj adres katalogu albo filmu vider.info: https://vider.info/dir/+dse1v51
Katalog docelowy (Enter = bieżący): D:\Filmy\Pokemon
Znaleziono filmów w katalogu: 81
   1. Pokemon Indigo League 01- Pokemon wybieram cię !
   2. Pokemon Indigo League 02- Ostry dyżur Pokemon
   ...
  81. Pokemon Indigo League 85- Niebezpieczny Pokeball
Od którego filmu zacząć? (numer, nazwa lub URL; Enter = od pierwszego): 5
Na którym filmie skończyć? (numer, nazwa lub URL; Enter = do ostatniego): League 07
Wybrano 3: od „Pokemon Indigo League 05- Spotkanie w Marmorii” do „Pokemon Indigo League 07- Wodne kwiaty Azurii”
Pobrać filmów: 3 do D:\Filmy\Pokemon? [T/n]
```

- W trybie interaktywnym film można wskazać także **numerem z listy**.
- Parametry podane w wierszu poleceń nie są odpytywane, np. `uv run advvidedl -o D:\Filmy` zapyta tylko o adres i zakres.
- Ctrl+C przerywa program w dowolnym momencie.

### Docker

```bash
docker build -t advvidedl .
```

Pobrane pliki trafiają do zamontowanego katalogu `/data`, czyli do bieżącego katalogu na hoście:

```bash
# PowerShell
docker run --rm -it -e DEEPSEEK_API_KEY -v "${PWD}:/data" advvidedl https://vider.info/dir/+dse1v51
docker run --rm -it -e DEEPSEEK_API_KEY -v "${PWD}:/data" advvidedl https://vider.info/dir/+dse1v51 -s "League 05" -e "League 07"
docker run --rm -it -e DEEPSEEK_API_KEY -v "${PWD}:/data" advvidedl https://vider.info/vid/+fxn8m5x
docker run --rm -it -e DEEPSEEK_API_KEY -v "${PWD}:/data" advvidedl      # tryb interaktywny

# bash
docker run --rm -it -e DEEPSEEK_API_KEY -v "$PWD:/data" advvidedl https://vider.info/dir/+dse1v51 -o pokemon
```

`-it` jest potrzebne do trybu interaktywnego i do ręcznego wpisania captchy. W trybie ręcznym obrazek captchy (`vider-captcha.png`) jest zapisywany w katalogu docelowym, więc widać go na hoście. Bez `-it` i bez adresu program wypisuje pomoc i kończy działanie.

## Wynik

- Pliki są nazywane według tytułów z katalogu (`<tytuł>.mp4`). Powtarzające się tytuły dostają dopisek ` [id]`.
- Istniejące pliki są pomijane, więc ten sam katalog można bezpiecznie pobierać ponownie.
- Przerwane pobieranie (`<tytuł>.mp4.part`) jest wznawiane przy następnym uruchomieniu.
- Kody wyjścia:
  - `0`: pobrano wszystko (albo `--dry-run`, albo rezygnacja w trybie interaktywnym),
  - `1`: coś się nie udało (captcha, sieć albo któryś plik),
  - `2`: błędne argumenty (np. nieznany film w `--start`),
  - `130`: przerwano (Ctrl+C).

## Jak to działa

- Captcha zabezpiecza tylko strony HTML i pojawia się już po kilku zapytaniach z jednego IP. Program pobiera tylko jedną stronę: listę katalogu albo stronę filmu. Captchę rozwiązuje w pętli, bo potrafi wrócić 2–4 razy także po poprawnej odpowiedzi.
- Kod w linku `/vid/+f<kod>` to zakodowane ID pliku (podmienione cyfry: `m n x s e 8 1 5 c v` = `0–9`). Dzięki temu nie trzeba otwierać strony każdego filmu.
- Filmy są pobierane z `https://stream.vider.info/video/<id>/v.mp4`. Ten serwer nie jest chroniony captchą. To wersja do odtwarzania online, często mniejsza niż rozmiar oryginału podany na stronie.

## Testy

```bash
uv run pytest
```
