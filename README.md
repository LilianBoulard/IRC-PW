This is an IRC client/server project. It is a proof of work,
and should not be used seriously.

# Énoncé

Le but de ce mini-projet est de réaliser un service de discussion en ligne (*Internet Relay Chat* ou IRC) en Python.
Il s’agit d’un système client/serveur permettant à des utilisateurs de discuter en direct en s’envoyant des messages.
Les utilisateurs peuvent discuter en groupe à travers des canaux de discussion, mais également deux-à-deux de manière *privée*.

Le principe est assez simple : des utilisateurs se connectent à un *serveur* IRC en utilisant un programme *client*,
tapent des commandes et le serveur exécute ces commandes. Le réseau IRC est constitué de serveurs connectés entre
eux, sans topologie particulière. Chaque client se connecte à un des serveurs et les commandes (ou messages) qu’il
tape sont communiquées par son serveur de rattachement aux autres serveurs, jusqu’aux clients destinataires. Les
commandes acceptées par un serveur sont assez nombreuses et tout est décrit dans un protocole décrit dans la
RFC1459 : https://datatracker.ietf.org/doc/html/rfc1459.

Le guide suivant décrit de manière succinte la grande majorité des commandes disponibles :
https://fr.wikipedia.org/wiki/Aide:IRC/commandes

Comme vous pouvez le voir, les commandes ont la forme suivante `/commande <arguments>`, où `<arguments>`
représente une liste d’arguments (cette liste pouvant être vide). 
Dans ce projet, nous allons implémenter un petit sous-ensemble de ces commandes. 
Chaque client est identifié par un surnom (nickname). Les noms de canaux
commencent par un symbole #.

- `/away [message]` - Signale son absence quand on nous envoie un message en privé
  (en réponse un message peut être envoyé). Une nouvelle commande `/away` réactive l’utilisateur.
- `/help` - Affiche la liste des commandes disponibles.
- `/invite <nick>` - Invite un utilisateur sur le canal où on se trouve
- `/join <canal> [clé]` - Permet de rejoindre un canal (protégé éventuellement par une clé). Le canal est créé s’il n’existe pas.
- `/list` - Affiche la liste des canaux sur IRC.
- `/msg [canal|nick] message` - Pour envoyer un message à un utilisateur ou sur un canal (où on est présent ou pas). 
  Les arguments `canal` ou `nick` sont optionnels.
- `/names [channel]` - Affiche les utilisateurs connectés à un canal. Si le canal n’est pas spécifié, affiche tous les utilisateurs de tous les canaux.

D’un point de vue utilisateur, un client IRC sera lancé sur la ligne de commande à l’aide du programme `irc.py` de la manière suivante :

```
python client.py nickname server_name
```

où `nickname` est le nom du client qui souhaite se connecter sur le serveur IRC `server_name`. 
Par exemple, cette commande peut lancer une interface graphique.

Cette interface serait composée de deux zones :
- Une zone pour afficher les messages des autres clients ;
- Une zone de saisie pour composer les messages et exécuter des commandes.

Les serveurs IRC seront lancés avec la commande suivante :

```
python server.py server_name [servers]
```

où `server_name` représente le nom du nouveau serveur IRC et `servers` est une liste (éventuellement vide) de
serveurs auxquels le nouveau serveur doit se connecter.

**Important**. Pour simplifier l’architecture de ce projet, les noms des serveurs seront simplement des numéros de
port. Tous les serveurs seront donc lancés sur l’adresse locale de vos machines (localhost).

**Première version du projet** : Dans cette première version, on utilisera un unique serveur IRC auquel tous les
utilisateurs vont se connecter. En interne, ce serveur doit donc gérer une liste de clients et une liste de canaux. On
implémentera toutes les commandes décrites ci-dessus.

**Deuxième version du projet** : Dans cette version, il s’agit de connecter plusieurs serveurs entre eux, de réaliser
l’acheminement des messages et des informations (liste des canaux, des utilisateurs présents dans ces canaux, etc.)
entre les serveurs.

# Design

## Client

The client is a simple software that just handles commands.  
When it is created, it is registered on the server.  
Commands entered by the human are submitted to the server the client is connected to.

## Server

The server doesn't have a GUI.  
When a client information is received, it is saved only on the server that received it.

## Technical notes

Queries are sent over the network with a custom format:
`command:<nickname>:<command>:<parameters>:<timestamp>`
- "command" is a constant
- `nickname` is the name of the client sending the command
- `command` is the name of the command, for example `away`
- `parameters` contains formatted arguments of the command, for `away` that might be a message
  ; this is an optional field
- `timestamp` is a UNIX epoch timestamp of the moment when this command was sent
Responses are sent over the network with this format:
`response:<nickname>:<content>:<timestamp>`
- "response" is a constant
- `nickname` is the name of the recipient
- `content` contains a human-readable string which is supposed to be printed to the user
- `timestamp` is a UNIX epoch timestamp of the moment this response was sent

## Limitations and issues

- There is no login security for users. Anyone can be impersonated.
- As such, multiple users can have the same nickname at the same time (though not on the same server). 
  Such a situation can cause a de-sync of messages (one might receive it but not other).
- Only works on a local machine. As stated by the *Énoncé*, server names are actually localhost port numbers.

# Usage

You will need python >= 3.9 to run this.
If you're on linux, use the following commands:
```commandline
$ [python3|python] --version
$ [python3|python] -m venv venv
$ source venv/bin/activate
$ python -m pip install --upgrade -r requirements.txt
$ bash ./setup_venv.sh
$ source venv/bin/activate
$ python [client|server].py
```

On Windows, the process is similar:

```commandline
>>> [py|python] --version
>>> [py|python] -m venv venv
>>> venv\Scripts\activate.bat
>>> python -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --upgrade -r requirements.txt
>>> python [client|server].py
```

It setups a dedicated environment in the `venv/` directory,
uses its interpreter, install the requirements, and finally,
you can run the client or the server.
