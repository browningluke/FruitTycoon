# Fruit Tycoon

#### Defining the problem

I spend a significantly large portion of my time on a server-based chat program called Discord, talking to my friends. It is used to communicate and is a great way to talk to and interact with friends over the internet. There is a moderation team on our server who manage what messages are sent, enforce rules and control who can access the server. I asked Caleb, a member of the moderation team, if there was anything I could make to improve quality of life on the server. He told me that a big issue that the moderation team are facing is that the members on the server were not engaged enough with each other and, as a result of that, the server was starting to die. He suggested that something be created that could help increase interaction between members in the server while also being enjoyable.

I discussed with him the fact that Discord provides a way for the users on a server to interact with non- human users which people can develop. My friends and I use them occasionally in other servers while talking, either for entertainment or solving a task.

He liked the idea of a Discord bot, suggesting that a game created with this framework could succeed in entertaining and encouraging cooperation between the people on the server. The solution would entail building a multiplayer text-based tycoon game in Python that will be able to interface with Discord and allow the users on the server to play it.

**Word Count**: 250

#### Justification

I chose to build a multiplayer tycoon game as it interacts nicely with how Discord is used. A user's main focus while on Discord is to communicate with others on the server, therefore the game should not be too user-intensive, requiring constant user input, as this will just become an annoyance. Also, the game should encourage users to interact with each other through gameplay, as teamwork can then be accomplished while users talk. A tycoon game is time-based, only allowing the user to harvest resources after a certain amount of time has passed, thus not requiring excessive input. The user could upgrade certain elements of their tycoon to allow for greater amounts of resource to be harvested after the time period. The use of a leaderboard and a trading mechanic will allow for teamwork and competition. The game will be text-based, as Discord is built as a chat-service, and thus does not support advanced GUI elements. Additionally, it will give the game a nice look as it goes in-line with user messages.

This game will be built in Python as it has the necessary APIs for interacting with Discord. This allows me to receive message data from, send messages to and generally interact with the users in the server. Further, it is a high-level, object oriented language which I am already familiar with. This provides the benefit that I am not learning the fundamentals as I go, and can write more efficient code than if I was not familiar.

**Word Count**: 249

#### Success Criteria

- User data is saved to and read from a file.
- Users can only harvest once a day.
- Raw materials can be refined into higher level goods.
- Users can send, accept and decline trades to/from other users.
- User’s multipliers can be upgraded with an increasing cost.
- Game posts leaderboard to server at specific time or when user runs command.
- Game help message contains detailed information about each command.
- Game has three difficulties (types) users can choose from.
