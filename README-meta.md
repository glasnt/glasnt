# What on earth is going on? 

My README.md is dynamically generated based on what my profile looks like. 

Every hour (see [.github/workflows/](.github/workflows), `build.py` is run to
dynamically generate my README.md based on current data from GitHub, and commit
that back to the repo. 

This repo requires access different to the included
[`GITHUB_TOKEN`](https://docs.github.com/en/actions/configuring-and-managing-workflows/authenticating-with-the-github_token#about-the-github_token-secret).
Generate a [personal access
token](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token)
with the default settings (public access), and save that token as a secret
called `API_TOKEN` against the repo. 

Idea and `build.yaml` from [simonw](https://github.com/simonw). 

Avatar art sources in `asciify.py`.

## Known issues, TODO

**Pinned repo forks are not always accurate**

Popular Repos sources from the top 6 repos from the user based on stars. But this edge type
has a field called forkCount, which includes (by the looks of it) forks of forks. The pinned 
repo type only has a `forks { totalCount }`, which is sometimes less than the forkCount

TODO: Add archived badge on archived repos

TODO: add test that at least check if the rendering succeeds 

TODO: possibly add more bio data (optional fields, etc)


## TODO


