import json
import os
import textwrap
from datetime import datetime, timezone

import emoji
from python_graphql_client import GraphqlClient


USERNAME = "glasnt"
GITHUB_TOKEN = os.environ.get("API_TOKEN", "")

client = GraphqlClient(endpoint="https://api.github.com/graphql")


def getnow():
    return datetime.now(timezone.utc)


def remove_emoji(text):
    return emoji.get_emoji_regexp().sub("", text)


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
        query=query, headers={"Authorization": "Bearer {}".format(GITHUB_TOKEN)},
    )
    return data

starttime = getnow()

# TODO make dynamic
# https://manytools.org/hacker-tools/convert-images-to-ascii-art/, width 32
avatar_art = """
              ...              
           .,,//. ..,(%@&       
           (     . ...*%%&%(    
                 .*(....,&#*,,  
           ..,../#&&%&&*,*.*.** 
  .       , .,*,/....#,,**,,//**
.           ., ,*(**,,,,**&%(/**
 .     .  ...../...(...,//(*&&/*
     . .###%&%&(.....,*//*,,#&&&
  .. .(%%%%%%%&%..**.,,,....&&& 
   . #%&%&%&&%&&&..,.......&&&  
     #&&%&&%&%&&&&%......&&#    
        (&&%%&&&&&&&&&&&
"""

userq = (
    """query
{
  user(login: "%s") {
    name
    login
    bio
    websiteUrl
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

avatar = flattable(avatar_art, w=36)
userblock = (
    avatar
    + "\n"
    + flattable(
        f"""
{data["name"]}
{data["login"]}

{short(data["bio"], w=36)}
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
            nameWithOwner, description
            primaryLanguage {
              name
            }
            stargazers {
              totalCount
            }
            forks {
              totalCount
            }
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

data = graphql(pinnedq)
pinned = []
for i, node in enumerate(data["data"]["user"]["pinnedItems"]["edges"]):
    n = node["node"]
    if "nameWithOwner" in n.keys():
        # is repo
        desc = remove_emoji(n["description"]).strip()
        desc1 = short(desc)
        desc2 = short(desc[len(desc1):].strip())
        pinned_block = textwrap.dedent(
            f"""[] {short(n["nameWithOwner"], p='')}\n
            {desc1}\n{desc2}\n\n{n["primaryLanguage"]["name"]} ✭ {n["stargazers"]["totalCount"]} ↡ {n["forks"]["totalCount"]}"""
        )
    else:
        # is gist
        text1 = ""
        text2 = ""
        if n["files"][0]["text"]:
            text = n["files"][0]["text"].split("\n")
            text1 = short(text[0])
            text2 = short(text[0][len(text1):])
                

        pinned_block = f"""<> {n["description"]}\n\n{text1}\n{text2}\n\n"""

    if i >= 2: 
        pinned.append(table(pinned_block, t=""))
    else:
        pinned.append(table(pinned_block))


pinnedheader = (
    " Pinned                                                                       ✨\n"
)



if len(pinned) < 6:
    pinned += [flattable("")] * (6 - len(pinned))

print(len(pinned))

pinnedblock = pinnedheader + sidebyside(pinned[0], pinned[1]) + sidebyside(pinned[2], pinned[3]) + sidebyside(pinned[4], pinned[5]) 
final = sidebyside(userblock, pinnedblock)

delta = getnow() - starttime

with open("README.md", "w") as f:
    f.write(f"```\n{final}\n```\n")

print(f"Generated in {delta} at {starttime}")
