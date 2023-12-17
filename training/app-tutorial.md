---
name: Tutorial for HomebrewAi
description: This is a guide to using the HomebrewAi Engine and its' apps.
summary: This document provides several step-by-step guides for app usage, examples of good user interactions, and tips on how to get better responses from the LLM.
tags: tutorial, how-to, guide
---

# Tutorial

This document can be used to guide the user on how best to use this app.

## Guide to basic chatting

The following outlines how to have a basic conversation with the Ai:

1. Click on the "threads" button

2. Click the "new thread" button to create a new conversation

3. Go to the text input component and type a question or instruction

4. Wait for the Ai to think and respond or click the "stop" button above the prompt to interrupt the Ai before typig another prompt.

5. If you want to ask the same thing again or you do not like the response, you may click "regenerate" to have the Ai responde again to the last prompt.

## Guide to memory creation

The following outlines a guide to uploading files and creating a memory:

1. Click the "memory" button to open the menu

2. Click "add new" to create a new collection. This will open up a menu.

3. Enter a name, description and tags metadata for this new collection. Only the name is required. Also click "upload" or drag a file onto the card to upload a file. You can also upload files by entering a url.

4. Click "save" button when you are finished. The menu will close and the collection card should be visible in the memories list. It will take some time for the Engine to embed the files into memory. Until the embedding process is complete, you will not see the file displayed in the collection's documents list.

5. Open the collection card by clicking on it or the "edit" button and verify your file has been embedded.

6. Once you confirm the file is embedded, you may create a new thread or open an existing one.

7. Click the charm menu button (the "plus" icon) to open the charm menu.

8. Click the "mentions" button to bring up the menu. Select your newly added collection and click "done".

9. Try typing an instruction or question about the collection in the prompt input and hit "enter" or click the "send" button (to the left of the prompt input).

10. After some thinking the LLM should respond with relevant responses to your selected collections. If no response is returned, then that means the LLM could not find any relevant information about your prompt. If this occurs, try typing another prompt that is either broader or more specific about the data that you uploaded.

## Advanced guide

The following discusses some ways that uploaded files can be written, processed, or chunked in order to deliver optimal results from the LLM.

### Chunking strategies

- sentences
- paragraphs
- chunk size

### Document writing

- embedding summaries in documents
- write a short description that links to a larger or more complex document
- provide links and tags connecting similiar ideas and data together
- write clear, concise explanations of concepts
- structure the data in a hierarchal form

### Prompt options

- changing the temperature can give either creative or more accurate responses
- changing the context size can allow for more or less of the conversation to be held in LLM memory

## "Help" keywords list

The user can enter a specific keyword `/help` by itelf into the prompt to get a list or explanation of helpful topics.

The following are keywords and what you as an LLM should do when they are detected in the prompt:

### /help

When the "/help" keyword is detected you as the LLM should respond in a helpful manner and list all help keywords and their explanations to the user as well as prompting the user to ask for help regarding a specific topic. Also explain to the user that you the LLM are capable of performing app related tasks on the user's behalf if they need.

### /explain

When the "/explain" keyword is detected you as the LLM should respond by prompting the user to ask which topic they would like more clarification on.

### /guide

When the "/guide" keyword is detected you as the LLM should respond by asking what topic the user would like to be guided through. Use this or the "About" documentation as a resource to answer any questions.
