from python_graphql_client import GraphqlClient
import os
import json
import textwrap 
import emoji

from datetime import datetime, timezone

def getnow():
    return datetime.now(timezone.utc)

starttime = getnow()

USERNAME = "glasnt"

def remove_emoji(text):
    return emoji.get_emoji_regexp().sub(u'', text)

GITHUB_TOKEN = os.environ.get("API_TOKEN", "")

def sidebyside(a, b):
    al = a.split("\n")
    bl = b.split("\n")

    if len(al) > len(bl):
        bl = bl +  [""] * (len(al) - len(bl))
    
    if len(bl) > len(al):
        al +=  [(len(al[0]) - 4) * " " ] * (len(bl) - len(al))

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

client = GraphqlClient(endpoint="https://api.github.com/graphql")
def graphql(query):
    data = client.execute(
        query=query,
        headers={"Authorization": "Bearer {}".format(GITHUB_TOKEN)},
    )
    return data


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

userq = """query
{
  user(login: "%s") {
    name
    login
    bio
    followers {
      totalCount
    }
    starredRepositories {
      totalCount
    }
  }
}
""" % USERNAME

resp = graphql(userq)
data = resp["data"]["user"]
followers = data["followers"]["totalCount"]
starred = data["starredRepositories"]["totalCount"]

avatar = flattable(avatar_art, w=36)
userblock = avatar +"\n" + flattable(f"""
{data["name"]}
{data["login"]}
{short(data["bio"], w=36)}
¤ {followers} followers · ✭ {starred} 
""", w=36)

pinnedq = """query
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
          }
        }
      }
    }
  }
}
""" % USERNAME

data = graphql(pinnedq)
pinned = []
for node in data["data"]["user"]["pinnedItems"]["edges"]:
    n = node["node"]
    if "nameWithOwner" in n.keys(): 
        pinned_block = textwrap.dedent(f"""
        [] {short(n["nameWithOwner"], p='')}
        {short(remove_emoji(n["description"]).strip())}

        {n["primaryLanguage"]["name"]} ✭ {n["stargazers"]["totalCount"]} ↡ {n["forks"]["totalCount"]}""")
    else:
        pinned_block = textwrap.dedent(f"""
        <> {n["description"]}


        """)
    
    pinned.append(pinned_block)


# hacks

pinnedheader = " Pinned                                                     Customize your pins\n"
pinnedblock = (pinnedheader + sidebyside(table(pinned[0]), table(pinned[1])) + 
              sidebyside(table(pinned[2], t=""), table(pinned[3], t="")) + 
              sidebyside(table(pinned[4], t=""), table(pinned[5], t="")))

final = sidebyside(userblock, pinnedblock)

delta = getnow() - starttime

with open("README.md", "w") as f:
    f.write(f"```\n{final}\n```\n<!--- generated in {delta} at {starttime} -->")
