import os
import httpx
import json
import textwrap 
from github import Github

# Automatically provided by GitHub Actions. For local testing, provide your own. 
# https://docs.github.com/en/actions/configuring-and-managing-workflows/authenticating-with-the-github_token#about-the-github_token-secret
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

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


def short(n, w=32, p=" .."):
    return textwrap.shorten(n, width=w, placeholder=p)

def table(s, w=40, l="|", r="|", t="_", b="_"): 
    ll = w - len(l) - len(r) 
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
        res.append(f"{l}{b * ll}{r}")
    return "\n".join(res)

def flattable(s, w=40):
    return table(s, w, l="", r="", t="", b="")


def graphql(query):
    json = {"query": query} 
    uri = "https://api.github.com/graphql"
    headers = {"Authorization": f"bearer {GITHUB_TOKEN}"}
    r = httpx.post(uri, headers=headers, json=json)
    return r.text 

g = Github(GITHUB_TOKEN)
user = g.get_user()
USERNAME = user.login

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
avatar = flattable(avatar_art)
print(avatar_art)
print(avatar)

userq = """query
{
  user(login: "%s") {
    followers {
      totalCount
    }
    following {
      totalCount
    }
    starredRepositories {
      totalCount
    }
  }
}
""" % USERNAME

resp = graphql(userq)
data = json.loads(resp)["data"]["user"]
followers = data["followers"]["totalCount"]
following = data["following"]["totalCount"]
starred = data["starredRepositories"]["totalCount"]

userblock = avatar + flattable(f"""
{user.name}
{user.login}
{user.bio}
¤ {followers} followers · {following} following · ✭ {starred} 

""", w=36)


pinnedq = """ query
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

resp = graphql(pinnedq)
data = json.loads(resp)
pinned = []
for node in data["data"]["user"]["pinnedItems"]["edges"]:
    n = node["node"]
    if "nameWithOwner" in n.keys(): 
        pinned_block = textwrap.dedent(f"""
        [] {short(n["nameWithOwner"], p='')}
        {short(n["description"])}

        {n["primaryLanguage"]["name"]} ✭ {n["stargazers"]["totalCount"]} ↡ {n["forks"]["totalCount"]}
        """)
    else:
        pinned_block = textwrap.dedent(f"""
        <> {n["description"]}



        """)
    
    res = table(pinned_block)
    pinned.append(res)


# hacks

pinnedheader = " Pinned                                                   Customize your pins\n"
pinnedblock = pinnedheader + sidebyside(pinned[0], pinned[1]) + sidebyside(pinned[2], pinned[3]) + sidebyside(pinned[4], pinned[5])

final = sidebyside(userblock, pinnedblock)
print(final)


