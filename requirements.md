You'll need to implement the streamlit interface of a guesser game.

Here're the requirements.

1. Core game logic. The game starts by picking a range of pre-defined objects as an item guess. This item will be prompt to an LLM together with the tasks. The user will ask the LLM about the details of the object, until they've input the correct answer (currently the user input contains the guess word, but can be altered), they win. LLM will need to answer the user's questions about the object, but not directly reveal the answer.
2. When the user sends the first request, the game timer starts.
3. When the user wins, the timer stops and will display the total elapsed time. A "new game" button will appear now to reset the game.
4. When the page is initially displayed, there will be no "new game" button. Just a chat input, and a hard coded AI message get displayed.

The file you will typically be modifying is `src/app.py`
