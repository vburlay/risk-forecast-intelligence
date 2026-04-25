from dash import html

from pack.ui.styles import (
    BIG_TITLE_STYLE,
    PAGE_STYLE,
    SECTION_STYLE,
)
from pack.ui.components import (
    section_title,
    description_card,
    logic_overview_block,
)


def render_description_tab():
    return html.Div(
        [
            html.H4("📘 Beschreibung & Interpretation", style=BIG_TITLE_STYLE),

            html.Div(
                [
                    section_title("Steuerung"),
                    description_card(
                        """
**Die operative Steuerung** zeigt die aktuelle Gesamtsituation des Systems auf einen Blick.

**Ziel der Sicht**
- aktuelle Belastung und Forecast-Abweichung sichtbar machen
- kritische Signale früh erkennen
- Teams mit erhöhtem Risiko priorisieren
- eine schnelle operative Einschätzung ermöglichen

**Interpretation der Kennzahlen**
- **Aktuelle Lücken-Tage** = Summe der aktuell beobachteten Lücken-Tage
- **Forecast-Abweichung** = aggregierte Differenz zwischen Ist und Forecast
- **Kritische Signale** = Anzahl auffälliger Team-Situationen
- **Teams mit erhöhtem Risiko** = Teams mit Status ungleich Normal
- **Maximales Risiko** = höchstes aktuell beobachtetes Gap-Signal
- **Gap** = Actual - Forecast
- **Zeit bis kritisch** = geschätzte Restzeit bis zum kritischen Schwellenwert auf Basis des aktuellen Verlaufs

**Business-Nutzen**
Diese Sicht dient als Einstiegspunkt für die operative Bewertung. Sie beantwortet die Frage, ob aktuell Handlungsbedarf besteht und welche Teams priorisiert betrachtet werden sollten.
                        """
                    ),
                ],
                style=SECTION_STYLE,
            ),

            html.Div(
                [
                    section_title("Steuerungslogik im Überblick"),
                    logic_overview_block(),
                ],
                style=SECTION_STYLE,
            ),

            html.Div(
                [
                    section_title("Prognose"),
                    description_card(
                        """
**Die Prognoseansicht** zeigt den zeitlichen Verlauf von Ist-Werten und Forecast je Team.

**Ziel der Sicht**
- Entwicklung eines Teams über die Zeit nachvollziehen
- Abweichungen zwischen Ist und Prognose früh erkennen
- Forecast-Qualität operativ einordnen
- pro Team die aktuelle Risikodynamik bewerten

**Baseline Forecast / Referenzmodell**
Zusätzlich wird ein einfacher Referenzwert berechnet, der die erwartete Entwicklung unter stabilen Bedingungen beschreibt.

Der Baseline Forecast basiert typischerweise auf:
- gleitendem Durchschnitt
- einfachen Trendannahmen
- historischer Normalentwicklung

Er dient als Vergleichsbasis für die Bewertung der Prognose.

**Interpretation im Vergleich**
- **TAGEN vs Baseline** zeigt, ob eine Entwicklung ungewöhnlich ist
- **TAGEN vs Prognose** zeigt, ob die Prognose aktuell getroffen wird
- **Prognose vs Baseline** zeigt, ob das Modell eine Veränderung erwartet

**Interpretation der Kennzahlen**
- **Tage** = aktueller beobachteter Wert
- **Prognose** = erwarteter Wert
- **Baseline** = erwarteter Wert unter stabilen Bedingungen
- **Abweichung** = Differenz zwischen Ist und Prognose
- **Anomaliesignal** = Stärke der aktuellen Abweichung vom erwarteten Verlauf
- **Gap-Signal** = relative Stärke der Abweichung
- **Zeit bis kritisch** = geschätzte Restzeit bis zu einem kritischen Zustand
- **Risikostatus** = verdichtete operative Bewertung
                        """
                    ),
                ],
                style=SECTION_STYLE,
            ),

            html.Div(
                [
                    section_title("Anomalien"),
                    description_card(
                        r"""
**Warnsignale** sind Zeitpunkte, an denen sich die Anzahl der **TAGEN** deutlich vom üblichen Verlauf (**Trend**) unterscheidet.

Solche Abweichungen können auf besondere Ereignisse, Ausreißer oder ungewöhnliche Entwicklungen hinweisen.

Der Vergleich erfolgt relativ zur üblichen Schwankung über folgenden Score:

$$
\lvert score \rvert = \left| \frac{TAGEN - Trend}{Std} \right|
$$

**Bedeutung**
- **TAGEN** = beobachteter Ist-Wert
- **Trend** = geglätteter erwarteter Verlauf
- **Std** = Standardabweichung, also typische Schwankungsbreite
- **Score** = normierte Stärke der Abweichung

**Interpretation**
- niedriger Score: normale Schwankung
- mittlerer Score: beobachtungswürdige Abweichung
- hoher Score: potenzielles Warnsignal

**Hinweis**
Der letzte Tag kann vorläufig erhöhte Werte enthalten, da die Periode noch nicht abgeschlossen ist. Die Signale dienen daher in erster Linie der Orientierung und sollten fachlich geprüft werden.
                        """
                    ),
                ],
                style=SECTION_STYLE,
            ),

            html.Div(
                [
                    section_title("Risiko"),
                    description_card(
                        """
**Zukunftsrisiken** beschreiben die geschätzte Eintrittswahrscheinlichkeit eines kritischen Gap-Ereignisses innerhalb definierter Zeithorizonte.

Die fachliche Logik folgt der analytischen Kette:

**Operative Steuerung → Erwartete Entwicklung → Kritische Abweichungen → Zukunftsrisiko**

**Ziel der Sicht**
- Risiken über mehrere Zeithorizonte vergleichen
- kurzfristige und mittelfristige Gefährdung sichtbar machen
- Teams nach Dringlichkeit priorisieren
- operative Frühwarnsignale in eine Zukunftssicht übersetzen

**Bedeutung für das Business**
- **Operative Steuerung** zeigt die aktuelle Situation
- **Erwartete Entwicklung** beschreibt die wahrscheinliche Dynamik
- **Kritische Abweichungen** machen Instabilität sichtbar
- **Zukunftsrisiken** verdichten diese Informationen zu einer priorisierbaren Zukunftssicht

**Interpretation der Kennzahlen**
- **P(Gap in 30 Tagen)** = geschätzte Eintrittswahrscheinlichkeit innerhalb von 30 Tagen
- **P(Gap in 90 Tagen)** = geschätzte Eintrittswahrscheinlichkeit innerhalb von 90 Tagen
- **Erwartete Zeit bis zum Gap** = erwarteter Zeitraum bis zum nächsten kritischen Ereignis
- **Risikostatus** = zusammenfassende Bewertung der aktuellen Risikolage

**GAP event**
Ein GAP event ist ein kritisches Abweichungsereignis. Es beschreibt eine Situation, in der die beobachtete Entwicklung deutlich vom erwarteten Verlauf abweicht und fachlich relevant wird.
                        """
                    ),
                ],
                style=SECTION_STYLE,
            ),

            html.Div(
                [
                    section_title("Szenarien"),
                    description_card(
                        """
**Die Szenarioanalyse** erweitert das System um eine strukturierte What-if-Perspektive.

Sie zeigt, wie empfindlich das System auf alternative Entwicklungen reagiert.

**Ziel der Sicht**
- Auswirkungen möglicher Entwicklungen simulieren
- Sensitivität des Systems sichtbar machen
- Unterschiede zur Ausgangslage transparent vergleichen
- Risiken unter veränderten Rahmenbedingungen bewerten

**Verfügbare Szenarien**
- **Volumenanstieg** erhöht die Belastung direkt
- **Trendbeschleunigung** verschiebt die Dynamik in Richtung kritischer Entwicklung
- **Volatilitätsanstieg** verstärkt Schwankungen und Instabilität

**Interpretation**
- Wenn das Gap-Signal im Szenario deutlich steigt, reagiert das System empfindlich auf diese Veränderung.
- Wenn Teams vom Status Normal zu Beobachten oder Kritisch wechseln, entsteht zusätzlicher Handlungsbedarf.
- Wenn die Zeit bis kritisch sinkt, steigt die operative Dringlichkeit.

**Business-Nutzen**
Die Szenarioanalyse hilft zu verstehen, welche externen oder internen Veränderungen besonders riskant sind und wo frühzeitig Gegenmaßnahmen geplant werden sollten.
                        """
                    ),
                ],
                style=SECTION_STYLE,
            ),

            html.Div(
                [
                    section_title("Maßnahmen"),
                    description_card(
                        """
**Die Maßnahmenanalyse** bewertet konkrete Eingriffe und deren erwartete Wirkung auf Risiko, Status und Dringlichkeit.

**Ziel der Sicht**
- Handlungsoptionen transparent vergleichen
- erwartete Wirkung auf kritische Teams sichtbar machen
- Restrisiko nach Intervention abschätzen
- Priorisierung von Maßnahmen unterstützen

**Verfügbare Maßnahmen**
- **Reduktion der Lücken-Tage** senkt den aktuellen Belastungswert direkt
- **Stabilisierung** reduziert die Differenz zum Forecast
- **Forecast-Anpassung** verschiebt die Referenzbasis

**Interpretation**
- Sinkt das Gap-Signal nach der Maßnahme, wirkt die Maßnahme risikomindernd.
- Wechselt ein Team von Kritisch zu Beobachten oder Normal, verbessert sich die operative Lage.
- Bleibt das Restrisiko hoch, reicht die Maßnahme allein möglicherweise nicht aus.
- Je stärker die Maßnahme, desto größer sollte die erwartete Wirkung sein. Gleichzeitig sollte fachlich geprüft werden, ob diese Stärke realistisch umsetzbar ist.

**Business-Nutzen**
Die Maßnahmenanalyse unterstützt Entscheidungen unter Unsicherheit. Sie zeigt nicht nur, ob eine Maßnahme wirkt, sondern auch, wie stark sie wirkt und welches Restrisiko bestehen bleibt.
                        """
                    ),
                ],
                style=SECTION_STYLE,
            ),
        ],
        style=PAGE_STYLE,
    )