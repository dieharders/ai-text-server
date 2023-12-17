---
name: About HomebrewAi Knowledge App
tags: app, explanation
description: This document explains what the HomebrewAi Engine app is and what it can do.
summary: A user can upload files to ingest into the app and then instruct or ask questions to the LLM about the files.
---

# Knowledge Base engine

This is an application built for domain experts and knowledge workers. It provides tools to search, retrieve and ask questions about private data that the user has uploaded.

## Key capabilities

- Index documents uploaded manually or from a url. These documents can be text, audio, video, or other structured data (json).
- Search the index for keywords or phrases and return relevant results.
- Query the index for relevant data and synthesize a response based on a question or instruction.
- Summarize or analyze one or more documents.
- Provide a relevancy check on returned results to give the user an indication of how closely their query matches the results given.

## Application menus

There are four main menus to the app:

1. Chat prompt page

2. Knowledge base menu

3. Threads menu

4. Settings menu (accessible from user profile button)

### Chat page

If the coversation is new or has no history, you will see buttons to for pre-built conversation options. You may click on these to inject a pre-made prompt or start typing your own in the prompt input.

The following actions can be performed:

- Stop. You can prematurely stop the Ai from returning a response.
- Regenerate. This will resend the last prompt to the Ai for a new response.
- Open Charms menu. There is a "plus" icon to the right of the prompt input which you can click to bring up a drawer full of "charms". These are buttons that modify the current prompt or conversation in some way.

#### Charms menu

There are several buttons that change the behavior or style of the conversation. Currently, only the "mentions" button has functionality.

The entire list of charms are as follows:

- Microphone
- Mentions
- Prompt template (style of talking)
- Conversation mode (instruct or chat)
- System prompt (how LLM should behave)
- prompt options (temperature, context size, etc)

##### Mentions charm

When clicked a menu is brought up that displays a list of all collections. You may select one or more of these collections to be included in the context of the conversation.

When one or more collections are selected, the Ai will be informed not to consider any of its internal training data and only rely on the selected collection for in context information when responding.

While a collection is selected, the mentions charm will glow, letting you know it is active. You may hover over the mentions charm button to see a list of all currently selected collections.

### Threads Menu

This menu is accessed from the top banner, to the far left side. When opened it displays all saved conversations.

The following actions can be performed:

- Delete a single thread
- Delete all threads
- Share a link to a conversation
- Clicking on a thread displays the conversation on the prompt page

### Knowledge Base

This menu is accessed from the top banner, to the right of the threads menu button. When opened it displays all ingested collections of documents. Each collection can contain one or more documents (files).

The following actions can be performed:

- Delete a single collection
- Delete all collections and the database
- Add new document to collection. This opens a menu where you can enter a name, description, tags metadata and upload a file either from a url or disk.
- Copy the id of a collection
- Edit the collection

### Settings page

Here you can setup api keys for external services like database storage or LLM's, delete private data, and choose a specific LLM to use.

#### Editing a collection

When clicking on a collection card or the "edit" button on the card, it will bring up a menu that displays all the associated documents (files) that have been embedded in that collection as well as the description, tags and other metadata for that collection.

Each document card displays its' description, tags and other metadata. Documents can be removed from the current collection from this menu. Each document card has a "refresh" button that will re-ingest (embed) the file into the index if the source file has changed.

The following actions can be performed:

- Refresh. The document is re-embedded into the database if file has new changes.
- Remove the document from the collection

## How to setup

1. The HomebrewAi Engine app must first be installed and launched.

2. Once launched, you must download an LLM model using the model explorer menu.

3. After a model has been downloaded, click the "load" button on the model's card to select it for text inference.

4. Once a model is chosen you can bring up the HomebewAi web app and start interacting with the Ai.

## How to use

The primary use of this app is to interact with a chatbot in a conversational way.

It is supplemented by a feature called "memories" that allows the Ai to understand and recall the user's private data which would not otherwise be able to fit inside the Ai's memory context.

"Charms" provide a way to modfiy or add guard rails to the LLM responses. Using charms can facilitate novel ways of interacting with the Ai.

The HomebrewAi Engine is a server that uses normal http calls. Developers can write scripts or whole apps that utilize the Engine's endpoints to create new applications or use cases.

### How to format text documents for optimal query

It is best if a text document has a header that describes what the document is and how it can be used. Relevant tags should be added to help the Ai find and group other similiar information.

When writing the content, follow a similiar approach to note taking. Structure the text with headings, numbered lists and line breaks in order to illustrate the importance and relevance of data. The Markdown file format is a good option to use since it makes use of this notation style of writing.

Provide explicit details, examples and summaries in concise chunks so they can more easily be searched by the Ai.

## Use cases

- Onboarding new employees
- Asking specific questions about business processes, people or documentation
- Filter/parse through large amounts of data to find relevant information
- Summarize across similiar or disparate data
- Provide analysis or commentary on several pieces of information
- Destructure or re-structure data from external sources (using Function Calls or Grammar)
- Provide OCR on unstructured data. Can use Vision to detect and create summaries for images, chars, etc.
- Act as a research or coding assistant
- Act as a helpful and responsive Chatbot for employees, stake-holders, and customers
- Install as a plugin into a chat program like Slack or Discord in order to provide responses through a purely chat like interface.

## How it is built

The Engine is built with Python and FastAPI for the server and Next.js and Node.js for the front-end UI.

The web app is built with Next.js for UI, ChromaDB for vector embedding storage and Llama-Index for vector data retrieval.
