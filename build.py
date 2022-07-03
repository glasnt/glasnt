import json
import os
import textwrap
from datetime import datetime, timezone
import urllib.request
from asciify import asciify_runner
import emoji
from python_graphql_client import GraphqlClient


USERNAME = "glasnt"
GITHUB_TOKEN = os.environ.get("API_TOKEN", "")

client = GraphqlClient(endpoint="https://api.github.com/graphql")


def dedent(s):
    # textwrap.dedent is too forgiving for this purpose.
    res = ""
    for x in s.split("\n"):
        res += x.strip() + "\n"
    return res


def getnow():
    return datetime.now(timezone.utc)


def remove_emoji(text):
    if text:
        return emoji.get_emoji_regexp().sub("", text)
    else:
        return ""


def sidebyside(a, b):
    al = a.split("\n")
    bl = b.split("\n")

    if len(al) > len(bl):
        bl = bl + [""] * (len(al) - len(bl))

    if len(bl) > len(al):
        al += [(len(al[0])) * " "] * (len(bl) - len(al))

    if len(al) != len(bl):
        print(f"Blocks must be same height: {len(al)} vs {len(bl)}")
        breakpoint()

    res = []
    for n in range(len(al)):
        res.append(f"{al[n]}{bl[n]}")
    return "\n".join(res)


def short(n, w=32, p=""):
    if not n:
        return ""
    return textwrap.shorten(n, width=w, placeholder=p)


def table(s, w=40, l="|", r="|", t="_", b="_"):
    ll = w - len(l) - len(r)
    s = remove_emoji(s)
    lli = ll - 2
    res = []
    if t != "":
        res.append(f" {t * ll} ")
    for line in s.split("\n"):
        if len(line) > lli:
            nline = textwrap.shorten(line, width=lli, placeholder="").ljust(lli)
        else:
            nline = line.ljust(lli)
        res.append(f"{l} {nline} {r}")
    if b != "":
        res.append(f"{l}{b * ll}{r}\n")
    return "\n".join(res)


def flattable(s, w=40):
    return table(s, w, l="", r="", t="", b="")


def graphql(query):
    data = client.execute(
        query=query,
        headers={"Authorization": "Bearer {}".format(GITHUB_TOKEN)},
    )
    return data


starttime = getnow()

userq = (
    """query
{
  user(login: "%s") {
    name
    login
    bio
    websiteUrl
    avatarUrl
    followers {
      totalCount
    }
    starredRepositories {
      totalCount
    }
  }
}
"""
    % USERNAME
)

resp = graphql(userq)
data = resp["data"]["user"]
followers = data["followers"]["totalCount"]
starred = data["starredRepositories"]["totalCount"]

avatarUrl = data["avatarUrl"]
avatar_fn = f"{USERNAME}.png"
urllib.request.urlretrieve(avatarUrl, avatar_fn)

avatar = asciify_runner(avatar_fn, width=30)
avatar = flattable(avatar, w=36)

bio = "\n".join(textwrap.wrap(data["bio"], width=36))
userblock = (
    avatar
    + "\n"
    + flattable(
        f"""
{data["name"]}
{data["login"]}

{bio}

¤ {followers} followers · ✭ {starred} 

{data["websiteUrl"]}
""",
        w=36,
    )
)

pinnedq = (
    """query
{
  user(login: "%s") {
    pinnedItems(first: 6, types: [REPOSITORY, GIST]) {
      totalCount
      edges {
        node {
          ... on Repository {
            nameWithOwner
            description
            primaryLanguage {
              name
            }
            stargazers {
              totalCount
            }
            forks { totalCount } 
          }
          ... on Gist {
            description
            files(limit: 1) { text }
          }
        }
      }
    }
  }
}
"""
    % USERNAME
)

popularq = (
    """
{
  user(login: "%s") {
    repositories(first: 6, orderBy: {field: STARGAZERS, direction: DESC}, ownerAffiliations: OWNER) {
      edges {
        node {
          ... on Repository {
            nameWithOwner
            name
            description
            primaryLanguage {
              name
            }
            stargazers {
              totalCount
            }
            forkCount
          }
        }
      }
    }
  }
}

"""
    % USERNAME
)


data = graphql(pinnedq)
nodes = data["data"]["user"]["pinnedItems"]["edges"]
header = "Pinned"

# GitHub defaults to most popular self repos if there are no pinned
if data["data"]["user"]["pinnedItems"]["totalCount"] == 0:
    data = graphql(popularq)
    nodes = data["data"]["user"]["repositories"]["edges"]
    header = "Popular repositories"


pinned = []
for i, node in enumerate(nodes):
    n = node["node"]
    if "nameWithOwner" in n.keys():
        # is repo
        desc = remove_emoji(n["description"]).strip()
        desc1 = short(desc)
        desc2 = short(desc[len(desc1) :].strip())

        if header == "Pinned":
            name = short(n["nameWithOwner"], p="")  # Popular assumes current user
            fork_count = n["forks"]["totalCount"]
        else:
            name = short(n["name"], p="")
            fork_count = n["forkCount"]  # This doesn't appear in the pinned edge

        # Only display language if valid
        language = ""
        if n["primaryLanguage"]:
            language = n["primaryLanguage"]["name"]

        # Only display stars if there are stars
        stars = ""
        if n["stargazers"]["totalCount"] > 0:
            stars = f'✭ {n["stargazers"]["totalCount"]}'

        forks = ""
        if fork_count > 0:
            forks = f"↡ {fork_count}"

        pinned_block = dedent(
            f"""
            [] {name}

            {desc1}
            {desc2}

            {language} {stars} {forks}"""
        )
    else:
        # is gist
        text1 = ""
        text2 = ""
        if n["files"][0]["text"]:
            text = n["files"][0]["text"].split("\n")
            text1 = short(text[0])
            text2 = short(text[0][len(text1) :])

        pinned_block = dedent(
            f"""
            <> {n["description"]}

            {text1}
            {text2}

            """
        )

    if i >= 2:
        pinned.append(table(pinned_block, t=""))
    else:
        pinned.append(table(pinned_block))


if len(pinned) < 6:
    pinned += [flattable("")] * (6 - len(pinned))

header = " " + header.ljust(77) + "✨\n"

pinnedblock = (
    header
    + sidebyside(pinned[0], pinned[1])
    + sidebyside(pinned[2], pinned[3])
    + sidebyside(pinned[4], pinned[5])
)
final = sidebyside(userblock, pinnedblock)

delta = getnow() - starttime

with open("README.md", "w") as f:
    f.write(f"```\n{final}\n```\n")

print(f"Generated in {delta} at {starttime}")
