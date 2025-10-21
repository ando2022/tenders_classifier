#!/usr/bin/env python3
"""
Production Tender Classifier - Real Validated Model
Uses the best model from training phase (92% accuracy)
All-in-one file with complete embedded prompt
"""

import os
import json
import openai
from typing import Dict, List, Optional
from datetime import datetime

# ============================================================================
# COMPLETE EMBEDDED PROMPT - 92% Accuracy Model - UNABRIDGED
# ============================================================================

CLASSIFIER_PROMPT = """You are an expert consultant specializing in public-sector tenders for economic research and analysis.
Your goal is to review a new tender title (and optionally a short summary) and determine if it is a likely match
for the client based on the services, keywords, and past selections below.

## Client Services
# Services


## Datenportal

Das Datenportal von BAK Economics stellt alle wichtigen Wirtschaftsdaten auf Schweizer, kantonaler und kommunaler Ebene zur Verfügung. Dazu gehören beispielsweise die Bruttowertschöpfung, die Zahl der Arbeitsplätze in Vollzeitäquivalenten (VZÄ) und die Produktivität, die auch auf der Ebene der einzelnen Branchen abgefragt und im Excel-Format heruntergeladen werden können. Zusätzlich zu den historischen Daten werden auf dem Datenportal auch vierteljährlich aktualisierte Prognosen für die verschiedenen Variablen veröffentlicht.

Möchten Sie mehr über die Funktionsweise des Datenportals erfahren? Testen Sie es mit dem Gastzugang!

Für weitere Informationen oder spezielle Angebote kontaktieren Sie uns: info@bak-economics.com


## Wirtschaft Schweiz - Konjunkturprognosen Schweiz & Welt

Vom monatlichen Konjunkturbericht BAK Monthly Forecast über Webinars zu Spezialthemen oder individuelle Datenlieferungen. Unser Angebot im Bereich der Konjunkturprognose deckt verschiedene Vertiefungsgrade ab. Dabei steht die Wirtschaft Schweiz sowie die Weltwirtschaft im Fokus.


## Branchenanalyse - Marktpotenziale erkennen & nutzen

Ein wichtiger Faktor für die Entwicklung von Unternehmen sind branchenspezifische Einflüsse, mit welchen sich BAK seit 1980 in Form von Branchenanalysen beschäftigt. Hier geht es um branchenspezifische Prognosen und Risikoanalysen sowie den Einfluss struktureller Zusammenhänge oder wirtschaftspolitischer Rahmenbedingungen. Die breite Modell- und Analysestruktur dient auch als Ausgangspunkt für vertiefende Analysen von firmenspezifischen Fragestellungen und die Entwicklung von Lösungen. Vorteile einer Branchenanalyse
Strategiebegleitung

Fachliche Begleitung in strategischen wie auch operativen Prozessen inkl. fundierter Einordnung der Marktentwicklungen
Marktpotenzial erkennen und nutzen

Anhand Prognosekennzahlen und Analysen mit den BAK-Modellen
Chancen & Risiken erkennen

Beeinflussung von Technologien, wirtschaftspolitischen Entscheidungen und Strukturwandel
Angebotsübersicht
Wir bieten Lösungen für Schlüsselbranchen wie auch andere Teile der Wirtschaft an. Hier ein grober Überblick unseres Angebots.
BAK Analyseansatz
Alle Prognosen und Analysen basieren auf folgender Modellarchitektur.
Weitere Informationen
Wie wichtig ist die Branche aus volkswirtschaftlicher Sicht?
Mit der Branchenanalyse wird die Bedeutung der Branche durch eine modellgestützte Wirkungsanalyse belegt, somit die wirtschaftliche Aktivität der Branche im ganzheitlichen Wirtschaftskreislauf beleuchtet und aufgezeigt, wie andere Branchen davon profitieren.
Wie hat sich die Branche entwickelt und wie ist der Leistungsausweis einzuordnen?
Die Wachstumsanalyse zeigt den historischen Pfad einer Branche auf und analysiert die Einflussfaktoren für die beobachtete Dynamik. Neben dem Verlauf volkswirtschaftlicher Leistungskennziffern, wie Wertschöpfung oder Arbeitsproduktivität, wird auch die Entwicklung der Rahmenbedingungen nachgezeichnet. Veränderungen des Umfeldes spielen für die Entwicklung einer Branche eine treibende Rolle.
Wie können die intrasektoralen Unterschiede besser nachvollzogen werden?
Eine Untersuchung struktureller Aspekte gehört zum Kern einer Branchenanalyse: Die Auseinandersetzung mit den Teilsegmenten und Geschäftsfeldern, der Markt- und Grössenstruktur, der Humankapitalstruktur oder der regionalen Struktur bringt interessante Erkenntnisse hervor und trägt wesentlich zum Verständnis des Strukturwandels und dessen Auslösern bei. Das ist zur Erklärung der historischen Entwicklung von Bedeutung und beleuchtet wichtige Trends sowie Chancen und Risiken für die Zukunft.
Welchen Einfluss üben rechtliche und politische Rahmenbedingungen auf die Entwicklung der Branche aus?
Neben den wirtschaftlichen Rahmenbedingungen üben Standortbedingungen einen wesentlichen Einfluss auf die Wettbewerbsfähigkeit einer Branche aus. Mit einer theoretisch fundierten und quantitativ abgestützten Analyse der kausalen Wirkungszusammenhänge zwischen wirtschaftspolitischer Rahmenbedingungen, Wettbewerbsfähigkeit und wirtschaftlicher Entwicklung einer Branche kann für die Auswirkungen einzelner wirtschaftspolitischer Massnahmen sensibilisiert werden.
Was ist wichtig für eine Standortbestimmung?
Neben einem Performance-Check deckt der internationale Vergleich der Branchenanalyse branchenspezifische Erfolgsfaktoren auf und identifiziert die Bedeutung verschiedener Rahmenbedingungen und Standortfaktoren. Daraus lassen sich strategische Massnahmen auf Unternehmens- und Branchenebene sowie Handlungsempfehlungen für die Gestaltung wirtschaftspolitischer und standortbezogener Rahmenbedingungen ableiten.
Wie sind die Rahmenbedingungen sowie die Entwicklung der Branche zu beurteilen?
Die Branchenprognosen basieren auf Erkenntnissen zur Entwicklung konjunktureller Rahmenbedingungen und struktureller Fundamentalfaktoren. Von zusätzlichem Nutzen ist, dass die Modelle in ein umfassendes internationales Branchenmodell eingebettet sind, so dass neben regionalen auch globale Impulse berücksichtigt werden. Damit sind die Prognosen sowohl bei der Konjunkturprognose als auch bei der Projektion langfristiger Entwicklungspfade objektiv nachvollziehbar.


## Life Sciences (Pharma, Biotech, Medtech) - Prognosen & Analysen

Seit 1980 hat sich BAK Economics darauf spezialisiert, anhand unterschiedlicher Methoden Branchen und Regionen zu analysieren. Die Life Sciences beziehen sich auf die Herstellung medizinischer und lebensbewahrender Güter, wie zum Beispiel Medikamente, Impfstoffe und diagnostische und orthopädische Instrumente. BAK definiert die Life Sciences Branchen detaillierter als die übliche Branchenaufteilung in offiziellen Statistiken, was eine detailliertere Abbildung und ein langfristiges Monitoring der Branche im nationalen sowie im internationalen Vergleich erlaubt.
Ihr Nutzen
Strategiebegleitung
Fachliche Begleitung in strategischen wie auch operativen Prozessen inkl. fundierter Einordnung der Marktentwicklungen
Übersicht Marktentwicklung und Benchmarking eigene Performance
Zugang zu einer umfassenden und laufend aktualisierten Datenbank mit den wichtigsten Wirtschaftsindikatoren
Einordnung regionaler Rahmenbedingungen
Bewertung von Leistungen im Vergleich zu Konkurrenzregionen
Unser Angebot
Clusteranalysen - Kern des Monitorings ist eine umfassende Datenbank, welche Indikatoren zur Messung der wirtschaftlichen Leistungsfähigkeit und der Bedeutung der Life Sciences Industrie auf regionaler und nationaler Ebene enthält. Das Projekt umfasst momentan 16 internationale Regionen und 15 verschiedene Länder, die zeitliche Dimension erstreckt sich von 1980 bis zum jeweils vergangenen Jahr. Die den Projektträger*innen exklusiv zur Verfügung stehende Datenbank wird einmal pro Jahr aktualisiert. Bei Bedarf werden zusätzliche Standorte in die Datenbank integriert.
Global Pharma Monitor - Der Global Pharma Monitor bildet jederzeit alle Fakten zur Branche in gebündelter Form.

Aktuelle Einordnung der Branche (Indikatorik)
Aktuelle Perspektive im Konjunkturzyklus (Konjunkturprognose)
Orientierung: Langfristperspektive (Strukturprognose)
Hintergrundinformation (Makroökonomisches Umfeld)
Economic Briefing -Das Economic Briefing beinhaltet eine individuelle Analyse, Bewertung und Strategieberatung. Die Datengrundlage ist ein makroökonomisches, branchen- und firmenspezifisches Datenset.
Lohnverhandlung -Mit der gesammelten Erfahrung unterstützen wir Unternehmen der Life Sciences Branche bei der Erstellung einer faktenbasierten Analyse und Beratung zur Fundierung von Lohnverhandlungen.
Impact Analyse - Im Bereich des Economic Footprints bietet BAK modellgestützte Impact Analysen von wirtschaftlichen Aktivitäten, Ereignissen oder Tatbeständen auf die (regionale) Volkswirtschaft. Bei Studien im Marktfeld Volkswirtschaftliche Wirkungsanalysen steht auch der kommunikative Nutzen für den/die Kund*in im Vordergrund. Häufig geht es um Fragestellungen, die in öffentlichen und politischen Diskussionen aufgeworfen werden.


## Tourismus Schweiz - Prognosen & Analysen

Seit 1980 hat sich BAK Economics darauf spezialisiert, anhand unterschiedlicher Methoden Branchen und Regionen zu analysieren. Über Jahre konnte so fundiertes Wissen über den Tourismus Schweiz und international gesammelt werden. Innerhalb ihrer volkswirtschaftlichen Untersuchungen erstellt BAK Economics Prognosen und Analysen für den Tourismus Schweiz sowohl auf empirischer als auch auf quantitativer Ebene.
Ihr Nutzen
Strategiebegleitung
Fachliche Begleitung in strategischen wie auch operativen Prozessen inkl. fundierter Einordnung der Regional- und Marktentwicklungen.
Tourismus Impact messen
Einzigartiger Analyse-Ansatz, welcher die Berechnung der gesamten Effekte der Tourismusnachfrage in einer regionalen Wirtschaft ermöglicht.
Tourismus-Prognosen
Detaillierte und fundierte Prognosen für die Tourismuswirtschaft auf Ebene der Destinationen für eine bessere Planung.
Unser Angebot
Wir begleiten Destinationen in der Strategieberatung und Benchmarking im Bereich Tourismus. Tourismus Benchmarking
Zielsetzung der Benchmarking-Studien ist die Analyse des Erfolgs und der internationalen Wettbewerbsfähigkeit von Tourismusregionen und Destinationen. Dabei werden die spezifischen Erfolgsfaktoren der untersuchten Tourismusstandorte identifiziert, es werden Stärken-/Schwächenanalysen durchgeführt und Entwicklungsleitlinien aufgezeigt. Im Zentrum hierbei steht, neben verschiedener Analyse-Produkte und Beratungsdienstleistungen, die «BAK Tourism Intelligence®». Das Online-Tool ermöglicht ein internationales Benchmarking von Destinationen und Regionen. Diese können sich mit einem internationalen Sample vergleichen und auf diese Weise eigene Stärken und Schwächen selbst ermitteln.
Tourismus Impact Studien
Mittels eines ökonomischen Impact Modells wird die Bedeutung der gesamten Tourismuswirtschaft, eines Projekts oder eines Tourismusbetriebs für die regionale Wirtschaft untersucht. Die durch die touristische Nachfrage generierten Wertschöpfungs- und Beschäftigungseffekte werden geschätzt und analysiert.
Tourismusprognosen
Gestützt auf statistisch-ökonomischen Modellen werden Prognosen für Tourismusregionen und Destinationen erstellt. Tourismusprognosen liefern zentrale Entscheidungsgrundlagen, um den Tourismussektor noch gezielter auf die neuen und zukünftigen Herausforderungen des Weltmarktes auszurichten. Dank der Einbindung in die Modellwelt von BAK Economics können detaillierte und fundierte Konjunkturprognosen für die Tourismuswirtschaft entwickelt und umgesetzt werden.
Benchmarking Analyse-Tools
Die «BAK Tourism Intelligence®» ermöglicht ein einfaches, umfassendes und graphisch ansprechendes internationales Benchmarking von Destinationen und Regionen.
Wirtschaftspolitik- & Strukturanalysen
Die Wirtschaftspolitik- und Strukturanalysen liefern, gestützt auf empirischen Untersuchungen, Antworten auf tourismusspezifische volkswirtschaftliche und wirtschaftspolitische Fragestellungen. Im Fokus der Arbeiten stehen branchen- und wirtschaftsraumspezifische Analysen auf regionaler, nationaler und internationaler Ebene.
Lohnverhandlung
Mit der gesammelten Erfahrung unterstützen wir Unternehmen der Life Sciences Branche bei der Erstellung einer faktenbasierten Analyse und Beratung zur Fundierung von Lohnverhandlungen.
Impact Analyse
Im Bereich des Economic Footprints bietet BAK modellgestützte Impact Analysen von wirtschaftlichen Aktivitäten, Ereignissen oder Tatbeständen auf die (regionale) Volkswirtschaft. Bei Studien im Marktfeld Volkswirtschaftliche Wirkungsanalysen steht auch der kommunikative Nutzen für den/die Kund*in im Vordergrund. Häufig geht es um Fragestellungen, die in öffentlichen und politischen Diskussionen aufgeworfen werden.


## Finanzbranche Schweiz - Prognosen & Analysen

Seit 1980 hat sich BAK Economics darauf spezialisiert, anhand unterschiedlicher Methoden Branchen und Regionen zu analysieren. In vielen Metropolen Europas hat sich die Finanzbranche zu einer wichtigen Säule von Wertschöpfung und Wohlstand entwickelt. Innerhalb ihrer volkswirtschaftlichen Untersuchungen erstellt BAK Economics Prognosen und Analysen für die Finanzbranche Schweiz sowohl auf empirischer als auch auf quantitativer Ebene, wobei Banken und Versicherungen getrennt voneinander analysiert werden.
Ihr Nutzen
Strategiebegleitung
Fachliche Begleitung in strategischen wie auch operativen Prozessen inkl. fundierter Einordnung der Marktentwicklungen
Einordnung regionaler Rahmenbedingungen
Vergleich der konkurrierenden Finanzzentren und Herausarbeitung von Performance-Indikatoren, Marktpotenzial und Rahmenbedingungen
Benchmarking
Erhebung nationaler und auch abgegrenzter Daten von verschiedenen Finanzplatzstandorten als gute Indikatoren für den jeweils führenden Finanzplatz
Unser Angebot
«Monitoring Financial Centers»
Im Projekt «Monitoring Financial Centers» werden verschiedene konkurrenzierende Finanzzentren beschrieben und miteinander verglichen. Dabei wird die Branche Finanzdienstleistungen untergliedert in Banken, Versicherungen und übrige Finanzdienstleistungen mit sehr detaillierter Darstellung der Performance und deren Analyse.

Indikatoren - Performance & Rahmenbedingungen
Im Finanzsektor klaffen die üblichen volkswirtschaftlichen Performance-Indikatoren und die in der Branche selbst mehrheitlich verwendeten Indikatoren weit auseinander. Deshalb werden beide Aspekte berücksichtigt. Die natürlichen Marktbegrenzungen (geographisch, national, kulturell) werden gemessen und miteinander verglichen. Eine wichtige Rolle spielt auch die Steuergesetzgebung, da durch Steuern einerseits das insgesamt verfügbare Volumen verändert wird, andererseits ein Keil zwischen die erbrachte Dienstleistung des Finanzsektors und den Nutzen des/der Kund*in getrieben wird.

Standorte
Die folgende Auflistung gibt eine Übersicht über die für das Projekt relevanten Finanzplätze:

Schweiz (Zürich, Genf, Tessin, Basel)
Deutschland (Frankfurt)
Frankreich (Paris)
Österreich (Wien)
Italien (Mailand)
Liechtenstein (Vaduz)
Spanien (Madrid)
Niederlande (Amsterdam)
Luxemburg
Vereinigtes Königreich (London, Edinburgh)
Irland (Dublin)
USA (New York, Chicago)
Japan (Tokyo)
China (Hongkong, Shanghai)
Singapur

Prognosen
Dank der Einbindung in die Modellwelt von BAK Economics, bestehen detaillierte und fundierte Prognosen für die Finanzbranche Schweiz.
Branchenportrait
Das Branchenportrait kann zwei Komponenten enthalten. Zum einen die Schweiz unterteilt in Regionen und zum anderen eine Region im Fokus. Die Detaillierungsstufe und Definition der Region wird in einem Gespräch spezifiziert.
Lohnverhandlung
Mit der gesammelten Erfahrung unterstützen wir Unternehmen der Finanzbranche bei der Erstellung einer faktenbasierten Analyse und Beratung zur Fundierung von Lohnverhandlungen.

Impact Analyse
Im Bereich des Economic Footprints bietet BAK modellgestützte Impact Analysen von wirtschaftlichen Aktivitäten, Ereignissen oder Tatbeständen auf die (regionale) Volkswirtschaft. Bei Studien im Marktfeld Volkswirtschaftliche Wirkungsanalysen steht auch der kommunikative Nutzen für den/die Kund*in im Vordergrund. Häufig geht es um Fragestellungen, die in öffentlichen und politischen Diskussionen aufgeworfen werden.


## Prognosen zur Baukonjunktur Schweiz für Strategie, Budget und Benchmarking

Das ideale Tool für Ihre Strategie, Budgetabsicherung und Benchmarking der eigenen Unternehmensperformance. Jahresprognosen zur Baukonjunktur Schweiz auf Ebene:

Infrastruktur-, Wohn- & Betriebsbauten (unterteilt in 12 Unterbauarten und Neubau, Umbau & Renovation + Anzahl neu erstellte Wohnungen (Ein- & Mehrfamilienhäuser)) sowie
Grossregionen (Bassin Lémanique, Espace Mittelland, Basel, Zürich/Aargau, Zentralschweiz, Ostschweiz, Südschweiz)
Sichern Sie sich ab durch fundierte Datenbanken und -modelle von BAK Economics inkl. Excel- und Powerpointdokumente für die interne Weiterverwendung.

Ihr Nutzen
Absicherung Strategie
Weitsicht mit langfristigen Prognosen: 6-Jahresprognose über die Bautätigkeiten in der Schweiz und Grossregionen pro Sparte Wohn, Betrieb, Infrastruktur und Untersparten
Absicherung im Budgetierungsprozess
Marktprognosen bei der Budgetierung berücksichtigen
Benchmarking Unternehmensentwicklung
Eigene Entwicklung mit dem Markt vergleichen auf Ebene Bausparten und Grossregion
Wirtschaftliche Zusammenhänge erkennen
Bessere Einschätzung der übergeordneten Rahmenbedingungen für die Baubranche / Bauwirtschaft Schweiz
Übersicht regionaler Entwicklungen
Klarheit über regionale Potenziale und daraus ableitende Marktbearbeitung
Strategiebegleitung
Fachliche Begleitung in strategischen wie auch operativen Prozessen inkl. fundierter Einordnung der Marktentwicklungen


## MEM Industrie - Analysen & Beratung

Seit 1980 hat sich BAK Economics darauf spezialisiert, anhand unterschiedlicher Methoden Branchen und Regionen zu analysieren. Mit der gesammelten Erfahrung unterstützen wir bei der Erstellung einer faktenbasierten Analyse und Beratung für die MEM Industrie.
Ihr Nutzen
Marktpotenzial erkennen und nutzen
Erfahren Sie mehr über Ihre Wachstumsmärkte und die Schlüsseltechnologien der Zukunft für eine höhere Betriebseffizienz.
Einordnung der Rahmenbedingungen
Wie wirken sich Veränderungen der wirtschaftlichen und politischen Rahmenbedingungen in Ihren Absatzmärkten auf die Umsatzentwicklung Ihres Unternehmens aus?
Risiken rechtzeitig erkennen
Klarheit über verschiedene Unsicherheiten, die Ihr Unternehmen betreffen, effizienteres Risikomanagement und unternehmerische Resilienz.
Strategiebegleitung
Fachliche Begleitung in strategischen wie auch operativen Prozessen inkl. fundierter Einordnung der Marktentwicklungen.
Unser Angebot
Branchenmonitor
Global MEM-Monitor
Risikoanalyse
Standortanalyse
Branchenportrait
Lohnverhandlung
Impact Analyse


## Detailhandel Schweiz - Prognosen & Analysen

Seit 1980 hat sich BAK Economics darauf spezialisiert, anhand empirischer Methoden Branchen und Regionen zu analysieren. Der Detailhandel Schweiz gehört dabei seit Beginn zu den analysierten Schweizer Schlüsselbranchen.

Ihr Nutzen
Strategiebegleitung
Fachliche Begleitung in strategischen wie auch operativen Prozessen inkl. fundierter Einordnung der Marktentwicklungen.
Marktpotenzial erkennen und nutzen
Anhand Prognosekennzahlen und Analysen mit den BAK-Modellen.
Planungssicherheit bei Budgetierungen
Die Quartalsprognosen bieten einen Gesamtüberblick der Branche mit den wichtigsten Einflussfaktoren. Zusätzliche Prognosen über Preisentwicklungen runden das Angebot ab.
Unser Angebot
Quartalsprognosen
Unternehmensspezifische Prognosen
Schätzung des regionalen Marktpotenzials
Szenarienbasierte Prognosen
Struktur- und wirtschaftspolitische Analysen
Lohnverhandlung
Impact Analyse


## Regionalanalyse - Schweiz & International

Der intensiver werdende Standortwettbewerb stellt die Gemeinden, Städte und Regionen in der Schweiz und international, vor grosse Herausforderungen. Jede Region hat ihr eigenes wirtschaftliches, demografisches und geografisches Profil, aus dem sich individuelle Bedürfnisse und Handlungsnotwendigkeiten ableiten. BAK Economics liefert fundierte und auf die regionalen Bedürfnisse individuell zugeschnittene Daten und Analysen aus einer Hand – aktuell und effizient.

Vorteile einer Regionalanalyse
Am Puls der Entwicklung mit aktuellen Daten und Fakten
Behalten Sie die Übersicht in einer dynamischen Wirtschaftswelt: Erkennen Sie schneller die Veränderungen in Ihrer Region und den Konkurrenzregionen. Überprüfen Sie Ihre Strategien und justieren Sie diese nach.
Einordnung regionaler Entwicklungen und Rahmenbedingungen
Identifizieren Sie die Stärken und Schwächen Ihrer Wirtschaftsregion im Vergleich mit Konkurrenz- und Referenzregionen.
Argumentarien für Ihre Wirtschaftsregion
Überzeugen Sie interessierte Investor*innen von den Stärken Ihrer Region, vermitteln Sie Ihre Strategie und zeigen Sie der Öffentlichkeit, wohin sich Ihre Region entwickeln möchte.
Fundierte Strategieentwicklung
Unsere Daten und Analysen bilden ein solides Fundament für die Entwicklung einer tragfähigen regionalen Wirtschaftsstrategie. Lernen Sie die Eigenschaften Ihrer Region kennen, ihre Zukunftsfähigkeit einzuschätzen und die richtigen Weichen zu stellen.
Smart Specialisation
Nutzen Sie die neuesten Erkenntnisse der regionalwirtschaftlichen Forschung und Innovationstheorien, um Ihre Region noch zielgerichteter zu entwickeln.


## Known Keywords (non-exhaustive)
- domain: Analyse, BBL, BFS, Benchmarking, Bundesamt für, Bundesamt für Bauten und Logistik, Bundesamt für Statistik, Index, Kanton, Regionen, SECO, Staatssekretariat für Wirtschaft, Studie, Wirtschaft, Wirtschaftsberatung, Wirtschaftsforschung, Ökonomie


## Examples of Previously Selected Tender Titles
- Regulierungsfolgenabschätzung zum Umsatzschwellenwert für die Eintragungspflicht in das Handelsregister - Analyse der volkswirtschaftlichen Auswirkungen
- (18113) 341 Wie können wissenschaftlich fundierte Sachverhalte glaubwürdig, nachhaltig, zielgruppengerecht und zielführend kommuniziert werden?
- Regulierungsfolgenabschätzung zur Schaffung einer gesetzlichen Regelung von Trusts in der Schweiz - Analyse der volkswirtschaftlichen Auswirkungen
- (18261) 318 Analyse der Preise und der Qualität in der Hörgeräteversorgung
- Erwerbstätigkeit über das ordentliche Rentenalter hinaus
- (19129) 812 Branchenszenarien inkl. Regionalisierung: Entwicklungen bis 2060
- Regulierungsfolgenabschätzung zur Einführung einer Zielvorgabe für die Kostenentwicklung in der obligatorischen Krankenpflegeversicherung (OKP)
- (19141) 812 Schweizerische Verkehrsperspektiven 2050
- Kantonale volkswirtschaftliche Kennzahlen, Standortfaktoren und Prognosen
- Ausschreibung von volkswirtschaftlichen Studien zum Thema Tiefzinsumfeld und Investitionen
- (22193) 704 Durchführung der Umfrage zur Konsumentenstimmung 2023-2027
- Wirkungsmonitoring Innosuisse
- Vor- und nachgelagerten Wertschöpfungsstufen der Landwirtschaft
- Nutzung und Wirkung von Zwischenverdiensten
- Situation, Entwicklung und Vermeidung von Langzeiterwerbslosigkeit und Aussteuerungen
- Prognosen zu der Entwicklung der Anzahl der Stellensuchenden und Taggeldbezüger 2020-2023
- Monitoringevaluation
- Wirkungsevaluation
- Tourismus
- Gesundheitssektor
- Wirkungsbewertung des Programms Interreg V Oberrhein
- SBB Bewertung Nationaler Entwicklungsplan
- REK für die Region Nordschwarzwald
- Studie Wertschöpfung-Beschäftigung
- Prüfung zur Einführung eines Schweizer Innovationsfonds - RFA
- Wertschöpfung Tourismus Graubünden 22/23
- Arbeitsplatzbeschaffung durch Förderung erneuerbarer Energien und Energieeffizienz
- ICC Indexarbeiten/Webtool_updates für 2022-2027 neuer Pool als Experte
- Thüringen Dekarbonisierung
- Explorative Studie zur Untersuchung geschlechtsspezifischer Lohndifferenzen von Frauen und Männern
- Studie zu Massnahmen zur verbesserten Nutzung von Freihandelsabkommen
- Analyse Programmgebiet Interreg Oberrhein
- Ausschreibung volkswirtschaftliche Auswirkungen der Digitalisierung in der Mobilität
- Scoping study
- Gutachten Blockchain-Technologie
- Machbarkeitsstudie Arbeitsland NÖ 2019
- Erstellung von Konjunktur- und Strukturberichten für NÖ 2020, 2021, 2022, 2023 uns 2024
- Innovationsregion Mitteldeutschland - Technologiefeldanalyse
- Market and economic research; polling and statistics
- Digital Innovation Hubs Network
- Industry Level Growth and Productivity Data with Special Focus on Intangible Assets
- Study on the Macroeconomics of the Energy Union
- Technologische und wirtschaftliche Analyse von Industrieverträgen in aktuellen und zukünftigen digitalen Wertschöpfungsketten - Smart 2018/0003
- Ausschreibung für die Entwicklung eines Tools zum Thema "Funktionale Stadtgebiete und Regionen in Europa".
- Technological Transformation and Transitioning of Regional Economies
- State of the European Territory
- Interregional Relations in Europe
- Gezielte Analyse "Metropolitan Industrial Spatial Strategies & Economic Sprawl"
- Study on Prioritisation in the National and Regional Research and Innovation Strategies for Smart Specialisation
- ESPON Developing a metropolitan-regional imaginary in Milan-Bologna urban region (IMAGINE)
- Effizienzpotenzial in der OKP
- Ergebnisse von öffentlicher und privater Forschung: Patente
- Forschung und Entwicklung in Staat und Wirtschaft
- Schwerpunktstudie „Vergleich der Innovationssysteme China und Deutschland"
- Evaluation des BMBF-Forschungsprogramms "IKT 2020 - Forschung für Innovationen
- Evaluierung der Außenwirtschaftsförderung im Rahmen des Operationellen Programms EFRE Thüringen 2014 bis 2020
- Evaluierung der Maßnahmen zur Steigerung privater Investitionen von Unternehmen im Rahmen des Operationellen Programms EFRE Thüringen 2014 bis 2020
- Analyse der Auswirkungen der Digitalisierung der deutschen Exportwirtschaft auf die Exportkreditgarantien des Bundes und der Handlungsoptionen zur Fortentwicklung des Instrumentariums
- Methodische und analytische Stärkung in aktuellen Fragen der Außenhandels- und ausländischen Investitionspolitik
- Begleitforschung zum Technologieprogramm "Smarte Datenwirtschaft" sowie zum KI Innovationswettbewerb
- Studie Empfehlungen zu Datengrundlagen und Methoden für die Evaluation der steuerlichen FuE-Förderung
- Studie zu Maßnahmen führender Exportnationen
- Untersuchung der volkswirtschaftlichen Bedeutung des deutschen Bahnsektors auf Grundlage ihrer Beschäftigungswirkung
- Schlüsseltechnologien und technologische Zukunftsfelder in den neuen Bundesländern: Bestandsaufnahme und Potentiale
- Schwerpunktstudie "Technologiemärkte"
- Studie zu makroökonomischen Effekten der Volksinitative für eine Schweiz ohne synthetische Pestizide
- Imzmir S3 Strategy
- SECO Wirkungsanalyse Zweitwohnungsgesetz
- Vorstudie zur Analyse des künftigen Bedarfs des Schweizer Arbeitsmarktes an ausländischen Arbeitskräften
- Wertschöpfungsbeitrag
- Aufsetzen eines Online Tool für den Intercultural Cities Index und der Pflege/Updaten dieses Tools.
- Innovationsbericht Nordrhein-Westfalen - Vollbericht
- Sozialhilfebezug in der Mehrjahresperspektive und im Lebensverlauf
- Evaluation der Integrationsmassnahmen zur Vorbereitung auf die berufliche Eingliederung
- Wirtschaftliche Situation von Personen mit einer IV-Rente
- Ausgestaltung und Determinanten des Rentenübergangs
- Die wirtschaftliche Situation der Bevölkerung im Erwerbs- und im Rentenalter
- Evaluation «Finanzhilfen für familienergänzende Kinderbetreuung» – Wirkung der Finanzhilfen für Subventionserhöhungen von Kantonen und Gemeinden
- Berechnung der volkswirtschaftlichen Kosten von Sucht
- Finanzierung der gemeinwirtschaftlichen Leistungen, Anlagenutzungskosten und Defizitdeckungen der Spitäler
- Die wirtschaftliche Situation von Familien in der Schweiz. Bedeutung von Geburt und Scheidung/Trennung
- Evaluation der Wirksamkeit, Umsetzung, Ergebnisse und Wirtschaftlichkeit der Förderung des Normenwesens an das Deutsche Institut für Normung
- Analyse der deutschen Exporte und Importe von Technologiegütern zur Nutzung erneuerbarer Energien und anderer Energietechnologiegüter
- Untersuchung und Analyse der Patentsituation bei der Standardisierung von 5 G
- Neue Beschaffungsmärkte identifizieren, Potenziale für die deutsche Wirtschaft nutzen, Wertschöpfungsketten ausbauen
- Maritime Wertschöpfung und Beschäftigung in Deutschland
- Big Data in der Makroökonomie
- Entwicklung und Messung der Digitalisierung der Wirtschaft am Standort Deutschland
- Evaluation des BMWi Förderprogramms gemäss der Richtlinie zu einer gemeinsamen Förderinitiative zur Förderung von Forschung und Entwicklung im Bereich der Elektromobilität vom 08.12.2017, die gemeinsam vom Bundeswirtschaftsministerium und Bundesumweltministerium veröffentlicht wurde.
- Studie zum deutschen Telekommunikationsmarkt im internationalen Vergleich (umfassende und aktuelle Lagebeschreibung/-analyse im Festnetz- und Mobilfunkbereich)
- Wirtschaftlichkeitslücke und Wertabschöpfung bei der GRWInfrastrukturförderung
- Machbarkeitsstudie über die Erstellung eines Produzentenpreisindexes für Dienstleistungen im Bereich der Finanz- und Versicherungsdienstleistungen
- Die Hürden gegen Ressourceneffizienz und Kreislaufwirtschaft abbauen

## Output format (strict JSON):
{
  "prediction": "Yes" or "No",
  "confidence_score": <0..100>,
  "reasoning": "<brief one-sentence explanation>"
}

## Decision rules:
1. **Broad economic research scope**: The client works on:
   - Economic analysis, forecasts, and modeling
   - Surveys, data collection, and statistical analysis
   - Impact studies (economic, social, employment)
   - Cost-benefit analysis and feasibility studies
   - Regional/sectoral economic development
   - Policy evaluation and recommendations
   
2. **What to SELECT (predict "Yes")**:
   - Tenders about economic/statistical **analysis, studies, research, evaluation**
   - Topics like: labor markets, income, costs, investments, productivity, growth, sectors, regions
   - Surveys or data collection for economic purposes
   - Even if the domain is specialized (e.g., CO2, healthcare, transport), if it requires **economic analysis**, select it

3. **What to REJECT (predict "No")**:
   - Pure IT development/software without research component
   - Construction, infrastructure works without economic analysis
   - Legal services, translations, logistics
   - Training, education delivery (not evaluation)
   - Goods procurement without analysis component

4. **Be inclusive for borderline cases**: If a tender could involve economic research or analysis, lean toward "Yes" with moderate confidence (60-75).

5. **Language-agnostic**: Focus on meaning, not keywords. Tenders in German, French, English, Italian are all valid.
"""

# ============================================================================
# CLASSIFIER CODE
# ============================================================================

class ProductionTenderClassifier:
    """Production tender classifier using the validated 92% accuracy model"""
    
    def __init__(self, api_key: str = None):
        if api_key:
            openai.api_key = api_key
        else:
            # Try to load from time.config
            config_paths = ['time.config', '../time.config', '../../time.config']
            api_key_from_config = None
            
            for config_path in config_paths:
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            api_key_from_config = config.get('openai_api_key')
                            if api_key_from_config:
                                print(f"✅ Loaded API key from {config_path}")
                                break
                    except Exception as e:
                        print(f"⚠️ Could not read {config_path}: {e}")
            
            # Use key from config or fall back to environment variable
            if api_key_from_config:
                openai.api_key = api_key_from_config
            elif os.getenv('OPENAI_API_KEY'):
                openai.api_key = os.getenv('OPENAI_API_KEY')
                print("✅ Loaded API key from environment variable")
            else:
                raise ValueError(
                    "OpenAI API key not provided. Either:\n"
                    "1. Pass api_key parameter: ProductionTenderClassifier(api_key='...')\n"
                    "2. Set in time.config: {\"openai_api_key\": \"...\"}\n"
                    "3. Set environment variable: export OPENAI_API_KEY='...'"
                )
        
        self.prompt = CLASSIFIER_PROMPT
        print(f"✅ Classifier initialized with complete embedded prompt ({len(self.prompt)} characters)")
    
    def extract_smart_description(self, full_text: str, title: str) -> str:
        """Extract smart description from full text (part of 92% accuracy model)"""
        if not full_text or not full_text.strip():
            return ""
        
        # Smart extraction logic based on training results
        # Remove noise and keep signal
        lines = full_text.split('\n')
        relevant_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip noise patterns
            if any(noise in line.lower() for noise in [
                'contact:', 'tel:', 'email:', 'phone:', 'fax:',
                'deadline:', 'submission:', 'tender number:',
                'reference:', 'notice number:', 'publication date:',
                'legal basis:', 'cpv code:', 'estimated value:',
                'currency:', 'language:', 'place of performance:'
            ]):
                continue
                
            # Keep signal patterns
            if any(signal in line.lower() for signal in [
                'objective', 'purpose', 'scope', 'description',
                'requirement', 'deliverable', 'outcome',
                'analysis', 'study', 'research', 'evaluation',
                'assessment', 'review', 'examination'
            ]):
                relevant_lines.append(line)
        
        # Join and limit to 1000 characters (as per training)
        smart_desc = ' '.join(relevant_lines)[:1000]
        return smart_desc

    def classify_tender(self, title: str, description: str = "") -> Dict:
        """Classify a single tender using Title + Smart Extraction (92% accuracy model)"""
        try:
            # Prepare input using smart extraction approach
            if not title or not title.strip():
                if description and description.strip():
                    input_text = f"Description: {description[:500]}"
                else:
                    input_text = "No title or description available"
            else:
                input_text = f"Title: {title}"
                if description and description.strip():
                    # Use smart extraction for better performance
                    smart_desc = self.extract_smart_description(description, title)
                    if smart_desc:
                        input_text += f". Description: {smart_desc}"
                    else:
                        input_text += f". Description: {description[:500]}"
            
            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Expert tender classifier for economic research tenders"},
                    {"role": "user", "content": f"{self.prompt}\n\nTender: {input_text}"}
                ],
                temperature=0,
                max_tokens=300
            )
            
            # Parse response
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            try:
                # Remove markdown code blocks if present
                if result_text.startswith('```'):
                    result_text = result_text.split('```')[1]
                    if result_text.startswith('json'):
                        result_text = result_text[4:]
                    result_text = result_text.strip()
                
                result = json.loads(result_text)
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parse error: {e}")
                print(f"Response was: {result_text[:200]}")
                # Fallback parsing
                result = {
                    "prediction": "No",
                    "confidence_score": 50,
                    "reasoning": f"Failed to parse response: {result_text[:100]}"
                }
            
            return {
                "prediction": result.get("prediction", "No"),
                "confidence": result.get("confidence_score", 50),
                "reasoning": result.get("reasoning", "No reasoning provided"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Classification error: {e}")
            return {
                "prediction": "No",
                "confidence": 0,
                "reasoning": f"Classification error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def classify_batch(self, tenders: List[Dict], rate_limit_delay: float = 0.5) -> List[Dict]:
        """Classify a batch of tenders"""
        results = []
        
        for i, tender in enumerate(tenders):
            print(f"📄 Classifying tender {i+1}/{len(tenders)}: {tender['title'][:50]}...")
            
            result = self.classify_tender(
                tender['title'], 
                tender.get('description', '')
            )
            
            # Add tender info to result
            result.update({
                'tender_id': tender.get('id', ''),
                'tender_title': tender['title'],
                'tender_url': tender.get('url', ''),
                'tender_source': tender.get('source', ''),
                'tender_date': tender.get('date', '')
            })
            
            results.append(result)
            
            # Rate limiting
            import time
            time.sleep(rate_limit_delay)
        
        return results


if __name__ == "__main__":
    print("🤖 Production Tender Classifier")
    print("=" * 60)
    print("Usage:")
    print("  from production_classifier import ProductionTenderClassifier")
    print("  classifier = ProductionTenderClassifier()")
    print("  result = classifier.classify_tender(title, description)")
    print("=" * 60)