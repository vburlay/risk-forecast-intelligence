from dash import html

from pack.ui.styles import (
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
            html.Div(
                [
                    section_title("Einordnung & aktueller Stand"),
                    description_card(
                        """
Diese Anwendung befindet sich aktuell in der Phase der fachlichen und technischen Stabilisierung.

Der Fokus liegt auf:
- Validierung der Anforderungen
- Stabilisierung der Datenflüsse
- Strukturierung der Dashboard-Sichten
- Abstimmung der fachlichen Risikologik
- Vorbereitung der Architektur für spätere Modelle

Aktuell werden Risikosignale regelbasiert und heuristisch abgeleitet. Die Modellierung für Prognose, Anomalieerkennung und Risikobewertung ist der nächste Ausbauschritt.

**Geplanter Modellpfad**
- **XGBoost** als teamübergreifendes Hauptmodell für Prognosen
- **Prophet** als Baseline und transparenter Referenzverlauf
- **Prophet-basierte Warnsignale** über Residuen oder Erwartungsintervalle
                        """
                    ),
                ],
                style=SECTION_STYLE,
            ),

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
- **Gap-Signal** = relative Abweichung zwischen aktuellem Wert und Prognose. Es zeigt die Größe der Abweichung im Verhältnis zur Erwartung.
- **Anomaliesignal** = Stärke der Abweichung im Verhältnis zur typischen Streuung. Es zeigt, ob eine Abweichung ungewöhnlich stark ist.
- **P(Gap in 30 Tagen)** = geschätzte Eintrittswahrscheinlichkeit innerhalb von 30 Tagen
- **P(Gap in 90 Tagen)** = geschätzte Eintrittswahrscheinlichkeit innerhalb von 90 Tagen
- **Erwartete Zeit bis zum Gap** = erwarteter Zeitraum bis zum nächsten kritischen Ereignis
- **Risikostatus** = zusammenfassende Bewertung der aktuellen Risikolage

**Unterschied zwischen Gap-Signal und Anomaliesignal**
- **Gap-Signal** beantwortet: Wie groß ist die Abweichung relativ zur Prognose?
- **Anomaliesignal** beantwortet: Wie ungewöhnlich ist diese Abweichung im Vergleich zur typischen Schwankung?

**GAP event**
Ein GAP event ist ein kritisches Abweichungsereignis. Es beschreibt eine Situation, in der die beobachtete Entwicklung deutlich vom erwarteten Verlauf abweicht und fachlich relevant wird.
                        """
                    ),
                ],
                style=SECTION_STYLE,
            ),

            html.Div(
                [
                    section_title("Simulation & Wirkung"),
                    description_card(
                        """
**Simulation & Wirkung** bündelt zwei Perspektiven in einer gemeinsamen Sicht:

- **Szenario** für strukturierte What-if-Analysen
- **Maßnahme** für konkrete Eingriffe und deren erwartete Wirkung

**Ziel der Sicht**
- Auswirkungen möglicher Entwicklungen simulieren
- Handlungsoptionen transparent vergleichen
- Sensitivität des Systems sichtbar machen
- Unterschiede zur Ausgangslage transparent vergleichen
- Risiken unter veränderten Rahmenbedingungen bewerten
- Restrisiko nach Intervention abschätzen

**Verfügbare Szenarien im Modus Szenario**
- **Volumenanstieg** erhöht die Belastung direkt
- **Trendbeschleunigung** verschiebt die Dynamik in Richtung kritischer Entwicklung
- **Volatilitätsanstieg** verstärkt Schwankungen und Instabilität

**Verfügbare Maßnahmen im Modus Maßnahme**
- **Reduktion der Lücken-Tage** senkt den aktuellen Belastungswert direkt
- **Stabilisierung** reduziert die Differenz zum Forecast
- **Forecast-Anpassung** verschiebt die Referenzbasis

**Interpretation**
- Wenn das Gap-Signal im Szenario deutlich steigt, reagiert das System empfindlich auf diese Veränderung.
- Sinkt das Gap-Signal nach der Maßnahme, wirkt die Maßnahme risikomindernd.
- Wechselt ein Team von Kritisch zu Beobachten oder Normal, verbessert sich die operative Lage.
- Bleibt das Restrisiko hoch, reicht die Maßnahme allein möglicherweise nicht aus.
- Je stärker die Maßnahme, desto größer sollte die erwartete Wirkung sein. Gleichzeitig sollte fachlich geprüft werden, ob diese Stärke realistisch umsetzbar ist.

**Business-Nutzen**
Die Sicht hilft zu verstehen, welche Entwicklungen besonders riskant sind und welche Maßnahmen die operative Lage verbessern können.
                        """
                    ),
                ],
                style=SECTION_STYLE,
            ),

            html.Div(
                [
                    section_title("Entscheidungshilfe"),
                    description_card(
                        """
**Entscheidungshilfe** übersetzt die aktuelle Risikolage und die simulierten Maßnahmen in eine konkrete Handlungsempfehlung.

**Ziel der Sicht**
- empfohlene Maßnahme sichtbar machen
- fachliche Begründung transparent darstellen
- erwartete KPI-Veränderungen zusammenfassen
- Alternativen und deren Folgen vergleichbar machen
- Unsicherheit der Empfehlung einordnen

**Logik**
Die Empfehlung ist regelbasiert. Das System vergleicht verfügbare Maßnahmen gegen die aktuelle Ausgangslage und priorisiert die Option, die kritische Teams, Gap-Signal und Restrisiko am stärksten reduziert.

**Vertrauen**
Vertrauen ist ein heuristischer Vertrauenswert. Er basiert auf der Stärke des erwarteten Effekts, dem Abstand zur zweitbesten Alternative und der Datenabdeckung. Er ist keine validierte statistische Wahrscheinlichkeit.

**Business-Nutzen**
Die Sicht unterstützt Entscheidungen unter Unsicherheit, ersetzt aber keine fachliche Freigabe. Sie macht transparent, welche Maßnahme aus Systemsicht aktuell den größten erwarteten Nutzen hat.
                        """
                    ),
                ],
                style=SECTION_STYLE,
            ),
        ],
        style=PAGE_STYLE,
    )
