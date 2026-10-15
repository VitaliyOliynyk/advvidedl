# advvidedl

Pobiera filmy z vider.info: cały katalog (np. `https://vider.info/dir/+dse1v51`), wybrany zakres filmów z katalogu albo pojedynczy film (np. `https://vider.info/vid/+fxn8m5x`). Gdy vider.info wyświetli captchę, odczytuje ją model DeepSeek (`deepseek-flash`). Jeśli to się nie uda, program prosi o wpisanie kodu w konsoli. Działa w systemach Windows i Linux, także w Dockerze.

## Instalacja

Wymagane są Python 3.11+ oraz [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Klucz DeepSeek

Wygeneruj klucz w serwisie https://platform.deepseek.com i ustaw go jako zmienną środowiskową:

```powershell
$env:DEEPSEEK_API_KEY = "sk-..."      # PowerShell
```
```bash
export DEEPSEEK_API_KEY="sk-..."      # bash
```

Możesz też skopiować plik `.env.example` do `.env` w katalogu, z którego uruchamiasz program, i wpisać w nim klucz. Bez klucza captchę trzeba wpisywać ręcznie.

## Tryby pracy

Tryb zależy od podanego adresu:

| Wywołanie | Tryb |
|---|---|
| adres `https://vider.info/dir/+d…` | **katalog**: wszystkie filmy albo zakres od `--start` do `--end` |
| adres `https://vider.info/vid/+f…` | **film**: jeden film |
| bez parametrów (lub bez adresu) | **interaktywny**: program pyta o brakujące dane |

Obsługiwane są też adresy w domenie `vider.pl` oraz adresy z przedrostkiem `www.`.

## Parametry

```
advvidedl [URL] [-s FILM] [-e FILM] [-o KATALOG] [--dry-run]
          [--ai-attempts N] [--max-captcha N] [--model MODEL] [-h]
```

| Parametr | Opis |
|---|---|
| `URL` | Adres katalogu albo filmu. Bez niego program działa w trybie interaktywnym |
| `-s`, `--start FILM` | Pierwszy film do pobrania (tylko w trybie katalogu). Domyślnie pierwszy film w katalogu |
| `-e`, `--end FILM` | Ostatni film do pobrania, włącznie (tylko w trybie katalogu). Domyślnie ostatni film w katalogu |
| `-o`, `--output KATALOG` | Katalog docelowy (domyślnie bieżący). Jeśli nie istnieje, zostanie utworzony |
| `--dry-run` | Tylko wyświetla listę filmów (ID, nazwa pliku, adres), niczego nie pobiera |
| `--ai-attempts N` | Liczba prób rozwiązania captchy przez DeepSeek, po których program poprosi o ręczne wpisanie kodu (domyślnie 4) |
| `--max-captcha N` | Maksymalna liczba prób rozwiązania captchy dla jednej strony (domyślnie 12) |
| `--model MODEL` | Model DeepSeek obsługujący obrazy (domyślnie `deepseek-flash`; można go też ustawić w zmiennej `DEEPSEEK_MODEL`) |
| `-h`, `--help` | Wyświetla pomoc z opisem parametrów i przykładami |

Wartość **`FILM`** w `--start` i `--end` można podać na dwa sposoby:
- jako **adres filmu**, np. `https://vider.info/vid/+fxn8xmn` (skopiowany z przeglądarki). Film musi należeć do podanego katalogu.
- jako **nazwę**: pełny tytuł albo jego fragment, np. `"League 05"`. Wielkość liter nie ma znaczenia, a rozszerzenie `.mp4` jest ignorowane. Jeśli fragment pasuje do kilku filmów, program je wypisze i poprosi o dokładniejszą nazwę. Nazwę ze spacjami trzeba ująć w cudzysłów.

Zasady wyboru zakresu:
- bez `--start` i `--end`: cały katalog,
- tylko `--start`: od wskazanego filmu do końca katalogu,
- tylko `--end`: od początku katalogu do wskazanego filmu,
- `--start` i `--end`: oba wskazane filmy i wszystkie filmy między nimi (w kolejności z katalogu).

## Przykłady

Przykłady używają polecenia `uv run advvidedl` uruchamianego w katalogu projektu. Równoważnie można użyć `uv run python -m advvidedl`, a po zainstalowaniu pakietu (`pip install .`) samego polecenia `advvidedl`.

Wszystkie filmy z katalogu, zapisywane w bieżącym katalogu:
```bash
uv run advvidedl https://vider.info/dir/+dse1v51
```

Wszystkie filmy z katalogu, zapisywane we wskazanym katalogu (jeśli nie istnieje, zostanie utworzony):
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

Od jednego wskazanego filmu do drugiego (włącznie). Filmy można wskazać nazwą albo adresem, także łącząc oba sposoby:
```bash
uv run advvidedl https://vider.info/dir/+dse1v51 -s "League 05" -e "League 07"
uv run advvidedl https://vider.info/dir/+dse1v51 -s https://vider.info/vid/+fxn8xmn -e "League 07"
```

Od początku katalogu do wskazanego filmu:
```bash
uv run advvidedl https://vider.info/dir/+dse1v51 --end "League 10"
```

Podgląd, co zostanie pobrane (bez pobierania):
```bash
uv run advvidedl https://vider.info/dir/+dse1v51 -s "League 05" -e "League 07" --dry-run
```
```
215201	Pokemon Indigo League 05- Spotkanie w Marmorii.mp4	https://stream.vider.info/video/215201/v.mp4?uid=0
215198	Pokemon Indigo League 06- Clefairy i kamień księżycowy.mp4	https://stream.vider.info/video/215198/v.mp4?uid=0
215203	Pokemon Indigo League 07- Wodne kwiaty Azurii.mp4	https://stream.vider.info/video/215203/v.mp4?uid=0
```

Pojedynczy film:
```bash
uv run advvidedl https://vider.info/vid/+fxn8m5x
uv run advvidedl https://vider.info/vid/+fxn8m5x -o filmy
```

Bez DeepSeek (captchę zawsze wpisuje się ręcznie):
```bash
uv run advvidedl https://vider.info/dir/+dse1v51 --ai-attempts 0
```

Pomoc:
```bash
uv run advvidedl --help
```

### Tryb interaktywny

Uruchom program bez parametrów. Program zapyta o adres, katalog docelowy i zakres filmów:

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
Wybrane filmy: 3, od „Pokemon Indigo League 05- Spotkanie w Marmorii” do „Pokemon Indigo League 07- Wodne kwiaty Azurii”
Pobrać wybrane filmy (3) do D:\Filmy\Pokemon? [T/n]
```

- W trybie interaktywnym film można wskazać także **numerem z listy**.
- Jeśli podasz tylko część parametrów (bez adresu), program zapyta wyłącznie o brakujące. Na przykład `uv run advvidedl -o D:\Filmy` zapyta o adres i zakres, ale nie o katalog docelowy.
- Ctrl+C w każdej chwili przerywa działanie programu.

### Docker

```bash
docker build -t advvidedl .
```

Pobrane pliki trafiają do katalogu `/data` w kontenerze, do którego zamontowany jest bieżący katalog hosta:

```bash
# PowerShell
docker run --rm -it -e DEEPSEEK_API_KEY -v "${PWD}:/data" advvidedl https://vider.info/dir/+dse1v51
docker run --rm -it -e DEEPSEEK_API_KEY -v "${PWD}:/data" advvidedl https://vider.info/dir/+dse1v51 -s "League 05" -e "League 07"
docker run --rm -it -e DEEPSEEK_API_KEY -v "${PWD}:/data" advvidedl https://vider.info/vid/+fxn8m5x
docker run --rm -it -e DEEPSEEK_API_KEY -v "${PWD}:/data" advvidedl      # tryb interaktywny

# bash
docker run --rm -it -e DEEPSEEK_API_KEY -v "$PWD:/data" advvidedl https://vider.info/dir/+dse1v51 -o pokemon
```

Opcja `-it` jest potrzebna w trybie interaktywnym i przy ręcznym wpisywaniu captchy. Obrazek captchy do przepisania (`vider-captcha.png`) jest zapisywany w katalogu docelowym, dzięki czemu można go otworzyć na hoście. Uruchomiony bez `-it` i bez adresu program tylko wyświetla pomoc i kończy działanie.

## Wynik

- Nazwy plików pochodzą z tytułów filmów (`<tytuł>.mp4`). Jeśli tytuły się powtarzają, do nazwy dopisywany jest identyfikator ` [id]`.
- Istniejące pliki są pomijane, więc ten sam katalog można bezpiecznie pobierać ponownie.
- Przerwane pobieranie (`<tytuł>.mp4.part`) jest wznawiane przy następnym uruchomieniu.
- Kody wyjścia:
  - `0`: sukces (wszystko pobrane, `--dry-run` albo rezygnacja w trybie interaktywnym),
  - `1`: błąd (captcha, sieć albo któryś z plików),
  - `2`: błędne argumenty (np. nieznany film w `--start`),
  - `130`: przerwanie (Ctrl+C).

## Jak to działa

- Captcha chroni wyłącznie strony HTML i pojawia się już po kilku zapytaniach z jednego adresu IP. Program pobiera tylko jedną stronę HTML: listę filmów z katalogu albo stronę filmu. Captchę rozwiązuje w pętli, bo może się ona pojawić ponownie 2–4 razy, nawet po poprawnej odpowiedzi.
- Kod w linku `/vid/+f<kod>` to zakodowane ID pliku: każda cyfra od 0 do 9 jest zastąpiona odpowiednio znakiem `m n x s e 8 1 5 c v`. Dzięki temu nie trzeba otwierać strony każdego filmu.
- Filmy są pobierane z adresu `https://stream.vider.info/video/<id>/v.mp4`, który nie jest chroniony captchą. Jest to wersja do odtwarzania online, więc plik bywa mniejszy niż rozmiar oryginału podany na stronie.

## Testy

```bash
uv run pytest
```
