# Dobot M1Pro SPIF application
Aplikacja pozwalająca na użycie robota Dobot M1Pro w celu zastosowania techniki SPIF (jednopunktowe formowanie przyrostowe). Przed rozpoczęciem każdego procesu SPIF należy ustawić trzpień robota na wysokości styku z blachą w miejscu, który będzie punktem środkowym koła, w którym opisane jest figura.  

__Nie jest możliwe rozpoczęcie ruchu, gdy robot znajduje się w pozycji początkowej - musimy nadać mu odpowiednią orientację ramienia. W przypadku błędu ID:22 trzeba zmienić orientację ramienia!!!__
Najlepszym sposobem na przerwanie działania funkcji jest wciśnięcie Disconnect - powoduje momentalne przerwanie działania przez przerwanie wysyłania poleceń spowodowane zerwaniem połączenia, po ponownym połączeniu nie trzeba takze wykonywać nowych kroków, by robot mógł znowu wykonywać polecenia jak przy wykorzystaniu funkcji __STOP__.
W przypadku wyskoczeniu błędu należy:
1. Clear Error + Reset Robot - opcjonalnie
2. Disconnect + Connect - odłączenie od robota (wyczyszczenie kolejki zadań)
3. Disable + Enable - reset robota
Po wykonaniu tych punktów robot powinien móc przyjmować nowe polecenia.
## UI
### Robot Connect
W sekcji __Robot Connect__ znajdują się 4 pola, które są bazowo wypełnione, by umożliwić połączenie z robotem Dobot M1 Pro.  
Pola, które możemy uzupełnić:
* IP Address - ustalenie adresu IP, z którego korzysta robot
* Dashboard Port - dzięki temu portowi jesteśmy w stanie zarządzać ustawieniami robota, takimi jak: prędkość, usuwanie błędów czy włączenie robota.
* Move Port - port umożliwiający przesyłanie funkcji ruchowych do robota
* Feedback Port - port umożliwiający przekazywanie przez robota informacji w czasie rzeczywistym
* Connect - połączenie do robota z użyciem ustalonego IP i portów, połączenie odblokowuje korzystanie z reszty funkcji  
### Dashboard Function
W sekcji __Dashboard function__ znajdują się funkcje pozwalające na zarządzanie robotem. Pola:
* Enable/Disable - pole pozwalające na włączenie/wyłączenie robota
* Reset Robot - zresetowanie kolejki robota, zastopowanie wykonywanych poleceń
* Clear Error - usunięcie błędów, jeśli problem już nie występuje, np. przy zbyt dalekim wysunięciu ramienia póki nie ustawimy ramienia w polu działania, usunięcie błędów nie rozwiąże problemu
* Speed Ratio - ustalenie prędkości robota w %, po zatwierdzeniu polem __Confirm__ nowa wartość zostaje przekazana do oprogramowania Dobota
* Digital Outputs Index - pozwala na wybranie indeksu narzędzia, z którego korzystamy. Po ustaleniu statusu w polu __Status__(On/Off) oraz zatwierdzeniu polem __Confirm__ przekazujemy informacje o przekazaniu odpowiedniego sygnału do narzędzia, np. włączenie sprężarki w celu zamknięcia ramion chwytaka
### Move Function
Funkcje umożliwiające ruch robota do ustalonego w polach punktu - po łuku, bądź linii prostej.
* X - odległość od podstawy robota (maksymalna wartość - 400)
* Y - odchylenie robota od pozycji początkowej (ramiona w linii prostej)
* Z - wysokość robota w mm (min. 5, max. 245)
* R - obrót trzpienia, kąt (min. -360, max. 360)
* MovJ - wykorzystuje pola: X, Y, Z, R do przesunięcia trzpienia robota do zadanego punktu ruchem łukowym
* Initial Position - wykonuje ruch MovJ do pozycji początkowej: X:400, Y:0, Z:200, R:0
* Move Type - wybór ruchu MovJ(ruch łukowy) albo MovL(ruch liniowy) dla ścieżki wczytanej z pliku
* Sync - możliwość włączenia synchronizacji(robot czeka na zakończenie obecnego ruchu przed przesłaniem kolejnego), przy prostych kształtach redukuje wibracje, przy tych bardziej zaawansowanych może znacznie wydłużyć proces
* CP - ustawienie poziomu swobodnego przejścia (interpolowanie punktów), przy kształtach z kątami prostymi zalecana wartość 0 ze wzlędu na występowanie zaokrąglenia rogów przy użyciu CP > 0. Dla kształtów okrąglejszych z wieloma punktami wymagane, by zredukować wibracje i szarpanie ramion robota w trakcie pracy.
* Select a File To Read - Wybór pliku ze ścieżką do wczytania - plik w formacie GCODE liczby rozdzielone spacją - jeden ruch = 3 liczby (X, Y, Z). Z w ścieżce powinno zaczynać się od wartośći 0 i stopniowo zmniejszać wartość.
* Execute Path From File - Wykonanie ścieżki, która jest zawarta w pliku wybranym w polu __Select a File To Read__, dodatkowo wykorzystuje pola __CP__, __Sync__ oraz __Move Type__.
### SPIF Functions
Funkcje odpowiadające za proces SPIF (jednopunktowego formowania przyrostowego). W celu rozpoczęcia należy ustawić trzpień robota w punkcie, który ma być punktem środkowym okręgu, w który wpisane będą kształty. Pola: 
* Type - wybór kształtu, na bazie którego formujemy blachę
* Diameter - średnica koła, w którym opisany jest kształt (w mm)
* Step - krok o jaki będziemy zmniejszać średnicę koła w każdej iteracji (w mm)
* Depth - głębokość jaką chcemy osiągnąć (w mm)
* Execute Pattern - rozpoczęcie procesu SPIF z wykorzystaniem ustalonych parametrów
* Make 4 Small Figures - rozpoczęcie procesu SPIF czterech mniejszych elementów z wykorzystaniem ustalonych parametrów (max. średnica 50 mm)
* Execute Pattern With Die - rozpoczęcie odwróconego procesu SPIF z wykorzystaniem ustalonych parametrów, zaczynamy proces od środka i zwiększamy głębokość wraz ze
zwikększaniem średnicy okręgu
* Show Plot - graficzne przedstawienie ścieżki, którą wykona robot w czasie procesu
* Show Plot Using Die - graficzne przedstawienie ścieżki, którą wykona robot w czasie odwróconego procesu
### Feedback
Zawiera informacje o stanie robota, zadanej prędkości oraz informacje o błędach i dziennik zdarzeń. Dodatkowo zawiera przyciski, które po przytrzymaniu pozwalają na zmianę położenia ramienia robota: X, Y, Z, R pozwalają na zmianę ruchu w systemie kartezjańskim a J1, J2, J3, J4 pozwalają na poruszanie poszczególnymi silnikami.
