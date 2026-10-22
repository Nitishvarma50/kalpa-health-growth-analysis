# Where to read, in the order that helps

Every link below was opened and checked on 19 October 2026. Read in this order: your own Week 1 and 2 notes, the tool documentation for the thing you are stuck on, the industry sources, then the wider reading. Note in the approach log any link you used, with the date.

## The tools you are using

| What | Link | Read for |
|---|---|---|
| pandas: merge, join, concatenate | https://pandas.pydata.org/docs/user_guide/merging.html | The `validate=` argument that raises on duplicate keys, and the `indicator=` column that shows which side each row came from. |
| pandas: groupby | https://pandas.pydata.org/docs/user_guide/groupby.html | Split, apply, combine, and named aggregations for the customer-style table. |
| PostgreSQL: joins and table expressions | https://www.postgresql.org/docs/current/queries-table-expressions.html | What each join type keeps and drops, in the database's own words. |
| PostgreSQL: window functions | https://www.postgresql.org/docs/current/tutorial-window.html | RANK, ROW_NUMBER and partitions, with runnable examples. |
| pytest: getting started | https://docs.pytest.org/en/stable/getting-started.html | The five minutes you need to run `tests/`. |
| GitHub: about pull requests | https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests | How a pull request, review and merge work. |
| GitHub: about git | https://docs.github.com/en/get-started/using-git/about-git | Branches, commits and why history matters. |
| GitHub: large files | https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github | The 100 MB limit and what to do about it. |
| GitHub: projects (the task board) | https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects | Setting up the four-column board. |
| GitHub: Codespaces overview | https://docs.github.com/en/codespaces/overview | What a fresh Codespace is, and why the cold run uses one. |
| Conventional Commits | https://www.conventionalcommits.org/en/v1.0.0/ | A commit-message convention many teams use. You do not have to adopt it; read it to see what a message is for. |

## The industry

| What | Link | Read for |
|---|---|---|
| Dr Lal PathLabs, corporate presentations | https://www.lalpathlabs.com/investors/investors-inside/corporate-presentation | How a listed diagnostics chain explains its own tree: patients, samples, realisation, home collection. |
| Dr Lal PathLabs, annual reports | https://www.lalpathlabs.com/investors/investors-inside/annual-report | The vocabulary a diagnostics board uses. |
| Metropolis Healthcare, Q1 FY27 earnings call transcript (NSE filing) | https://nsearchives.nseindia.com/corporate/METROPOLIS_10082026125026_Signed_SE_Intimation_Earning_Call_transcipt_Aug5_26.pdf | Management on volume growth, mix and "no price increase". The source of the numbers in the handbook. |
| Metropolis Healthcare on BSE | https://www.bseindia.com/stock-share-price/metropolis-healthcare-ltd/metropolis/542650/ | Filings and results, including investor presentations. |
| Dr Lal PathLabs on BSE | https://www.bseindia.com/stock-share-price/dr-lal-pathlabs-ltd/lalpathlab/539524/ | Filings and results. |
| Razorpay: settlements API | https://razorpay.com/docs/api/settlements/ | How a payment gateway separates orders, payments and settlements, and why a settlement bundles many payments. Brief C. |
| Google Analytics: comparing metrics between Universal Analytics and GA4 | https://support.google.com/analytics/answer/11986666 | Why the same visitors produce different session counts in two systems. Brief B. |

## The thinking

| What | Link | Read for |
|---|---|---|
| Lean Enterprise Institute: the five whys | https://www.lean.org/lexicon-terms/5-whys/ | The original habit, in two paragraphs. |
| Google SRE book: postmortem culture | https://sre.google/sre-book/postmortem-culture/ | Why a blameless record of what broke is worth more than a tidy story. The challenges log in practice. |
| Wainer, "The Most Dangerous Equation" (chapter PDF, Princeton University Press) | https://assets.press.princeton.edu/chapters/s8863.pdf | Why small groups crowd both ends of any ranking. Brief D, and every ranking you ever make. |
| Tu and Gilthorpe, "The most dangerous hospital or the most dangerous equation?" (BMC Health Services Research, 2007) | https://link.springer.com/article/10.1186/1472-6963-7-185 | The same idea applied to hospital league tables, with funnel plots as the fix. Brief D. |
| Blake, Nosko and Tadelis, "Consumer Heterogeneity and Paid Search Effectiveness" (NBER Working Paper 20171, 2014) | https://www.nber.org/papers/w20171 | eBay's experiments on whether its advertising caused anything. Brief E, and every campaign claim you will ever be shown. |

## How to read a source without losing the afternoon

- Read the examples, not the parameter list.
- Read one section to answer one question, then close it and write the answer in your own words in the log.
- If a page is older than the tool version you are using, check the version in the page header before trusting a function name.
- A forum answer without a date and a version is a rumour.
