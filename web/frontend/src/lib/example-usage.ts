/**
 * Example usage of the generated API client
 *
 * This file demonstrates how to use the generated API client.
 * You can delete this file once you understand the patterns.
 */

import { configureApiClient, setApiToken } from './api';
import { UserServiceService, LibraryServiceService, CardsService } from '../generated/api';

// 1. Configure the client when your app starts
function initializeApp() {
  // Use environment variable or hardcode during development
  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8080/api';
  configureApiClient(backendUrl);
}

// 2. Example: User login
async function loginUser(email: string, password: string) {
  try {
    const response = await UserServiceService.userServiceLogin({
      email,
      password,
    });

    // Store the token and configure the client
    const token = response.token;
    localStorage.setItem('authToken', token || '');
    setApiToken(token);

    return response;
  } catch (error) {
    console.error('Login failed:', error);
    throw error;
  }
}

// 3. Example: Fetch user's libraries
async function fetchLibraries() {
  try {
    const response = await LibraryServiceService.libraryServiceGetLibraries();
    return response.libraries || [];
  } catch (error) {
    console.error('Failed to fetch libraries:', error);
    throw error;
  }
}

// 4. Example: Create a new library
async function createLibrary(name: string) {
  try {
    const response = await LibraryServiceService.libraryServiceCreateLibrary({
      name,
    });
    return response.library;
  } catch (error) {
    console.error('Failed to create library:', error);
    throw error;
  }
}

// 5. Example: Get cards in a library
async function getCardsInLibrary(libraryId: string) {
  try {
    const response = await CardsService.cardsGetCards(libraryId);
    return response.cards || [];
  } catch (error) {
    console.error('Failed to fetch cards:', error);
    throw error;
  }
}

// 6. Example: Add a card to a library
async function addCard(libraryId: string, scryfallId: string, foil: boolean = false) {
  try {
    const response = await CardsService.cardsCreateCard(libraryId, {
      scryfallId,
      foil,
    });
    return response.card;
  } catch (error) {
    console.error('Failed to add card:', error);
    throw error;
  }
}

// Export for use in your components
export {
  initializeApp,
  loginUser,
  fetchLibraries,
  createLibrary,
  getCardsInLibrary,
  addCard,
};
