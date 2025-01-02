# Hääle akustiliste tunnuste visualiseerimise rakendus
Käesoleva bakalaureusetöö eesmärk oli luua töölauarakendus, mis lihtsustab GeMAPS
(eGeMAPS) akustiliste tunnuste kasutamist foneetilistes uuringutes. Rakendus võimaldab
helifailidest GeMAPS-tunnuste eraldamist, nende visualiseerimist erinevatel diagrammitüüpidel (ajatelje-, histogrammi-, karp-, radari- ja vokaalikaardi diagrammid) ning sarnasuse analüüsi, et leida kõige sarnasemad salvestised. Helifailide töötlemisel (OpenSMILE)
kasutatakse TextGridide andmeid, et võimaldada foneemide ja sõnade tasemel analüüsi.
Tunnuste ajaraamilised väärtused salvestatakse MongoDB dokumendipõhises andmebaasis.
Kasutajaliides luuakse PyQt raamistikus ning interaktiivsete graafikute genereerimiseks kasutatakse Plotly Pythoni teeki. Sarnasuse analüüsimeetoditena rakendatakse klasterdamist (KMeans) ja koosinussarnasuse arvutamist.


# Voice Acoustic Feature Visualization Tool
The aim of this bachelor’s thesis was to create a desktop application for analyzing acoustic
features of GeMAPS (eGeMAPS). The application allows extracting GeMAPS features
from audio files, visualizing them on different chart types (timeline, histogram, box, radar
and vocal map charts) and similarity analysis to find the most similar recordings. Audio
File Processing (OpenSMILE) uses data from TextGrids to allow phoneme and material
analysis. The extracted feature values are stored in a MongoDB document-based database.
The user interface is created in the PyQt Python framework and the Plotly library is used
to generate interactive graphs. Both clustering (KMeans) and cosine similarity calculation
are used as similarity analysis methods.
