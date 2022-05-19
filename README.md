# publishing_profiler
Analyze publishing output from Iowa State University

Takes Web of Science export file

Filters based on document type

Identifies records with an ISU corrsponding author (CA)
- user can turn CA only analysis on/off

Cleans publisher name variants

Makes set of plots
- Bar chart of number of publications by publisher

Look at OA status of publications

Presented as website, launched in [!Streamlit](www.streamlit.com)
(https://share.streamlit.io/eschares/publishing_profiler/main/publishing_profiler.py)

Note: may take a minute or two to load if the site hasn't been used in a while, Streamlit puts it "to sleep" after a week of inactvity to save resources.
