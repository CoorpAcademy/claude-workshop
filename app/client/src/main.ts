import './style.css'
import { api } from './api/client'

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
  initializeQueryInput();
  initializeFileUpload();
  initializeModal();
  loadDatabaseSchema();
});

// Query Input Functionality
function initializeQueryInput() {
  const queryInput = document.getElementById('query-input') as HTMLTextAreaElement;
  const queryButton = document.getElementById('query-button') as HTMLButtonElement;
  
  queryButton.addEventListener('click', async () => {
    const query = queryInput.value.trim();
    if (!query) return;
    
    queryButton.disabled = true;
    queryButton.innerHTML = '<span class="loading"></span>';
    
    try {
      const response = await api.processQuery({
        query,
        llm_provider: 'openai'  // Default to OpenAI
      });
      
      displayResults(response, query);
      
      // Clear the input field on success
      queryInput.value = '';
    } catch (error) {
      displayError(error instanceof Error ? error.message : 'Query failed');
    } finally {
      queryButton.disabled = false;
      queryButton.textContent = 'Query';
    }
  });
  
  // Allow Cmd+Enter (Mac) or Ctrl+Enter (Windows/Linux) to submit
  queryInput.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      queryButton.click();
    }
  });
}

// File Upload Functionality
function initializeFileUpload() {
  const dropZone = document.getElementById('drop-zone') as HTMLDivElement;
  const fileInput = document.getElementById('file-input') as HTMLInputElement;
  const browseButton = document.getElementById('browse-button') as HTMLButtonElement;
  
  // Browse button click
  browseButton.addEventListener('click', () => fileInput.click());
  
  // File input change
  fileInput.addEventListener('change', (e) => {
    const files = (e.target as HTMLInputElement).files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  });
  
  // Drag and drop
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
  });
  
  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
  });
  
  dropZone.addEventListener('drop', async (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    
    const files = e.dataTransfer?.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  });
}

// Handle file upload
async function handleFileUpload(file: File) {
  try {
    const response = await api.uploadFile(file);
    
    if (response.error) {
      displayError(response.error);
    } else {
      displayUploadSuccess(response);
      await loadDatabaseSchema();
    }
  } catch (error) {
    displayError(error instanceof Error ? error.message : 'Upload failed');
  }
}

// Load database schema
async function loadDatabaseSchema() {
  try {
    const response = await api.getSchema();
    if (!response.error) {
      displayCollections(response.collections);
    }
  } catch (error) {
    console.error('Failed to load schema:', error);
  }
}

// Display query results
function displayResults(response: QueryResponse, query: string) {
  const resultsSection = document.getElementById('results-section') as HTMLElement;
  const queryDisplay = document.getElementById('query-display') as HTMLDivElement;
  const resultsContainer = document.getElementById('results-container') as HTMLDivElement;

  resultsSection.style.display = 'block';

  // Display natural language query and MongoDB query
  queryDisplay.innerHTML = `
    <div class="query-display">
      <strong>Query:</strong> ${query}
    </div>
    <div class="mongodb-query">
      <strong>MongoDB Query:</strong> <code>${JSON.stringify(response.mongodb_query, null, 2)}</code>
    </div>
  `;

  // Display results table
  if (response.error) {
    resultsContainer.innerHTML = `<div class="error-message">${response.error}</div>`;
  } else if (response.results.length === 0) {
    resultsContainer.innerHTML = '<p>No results found.</p>';
  } else {
    const table = createResultsTable(response.results, response.fields);
    resultsContainer.innerHTML = '';
    resultsContainer.appendChild(table);
  }

  // Initialize toggle button
  const toggleButton = document.getElementById('toggle-results') as HTMLButtonElement;
  toggleButton.addEventListener('click', () => {
    resultsContainer.style.display = resultsContainer.style.display === 'none' ? 'block' : 'none';
    toggleButton.textContent = resultsContainer.style.display === 'none' ? 'Show' : 'Hide';
  });
}

// Helper function to format cell values for display
function formatCellValue(value: any): string {
  if (value === null || value === undefined) {
    return '';
  }

  if (typeof value === 'object' || Array.isArray(value)) {
    return JSON.stringify(value, null, 2);
  }

  return String(value);
}

// Create results table
function createResultsTable(results: Record<string, any>[], columns: string[]): HTMLTableElement {
  const table = document.createElement('table');
  table.className = 'results-table';
  
  // Header
  const thead = document.createElement('thead');
  const headerRow = document.createElement('tr');
  columns.forEach(col => {
    const th = document.createElement('th');
    th.textContent = col;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);
  
  // Body
  const tbody = document.createElement('tbody');
  results.forEach(row => {
    const tr = document.createElement('tr');
    columns.forEach(col => {
      const td = document.createElement('td');
      td.textContent = formatCellValue(row[col]);
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  
  return table;
}

// Display collections
function displayCollections(collections: CollectionSchema[]) {
  const collectionsList = document.getElementById('collections-list') as HTMLDivElement;

  if (collections.length === 0) {
    collectionsList.innerHTML = '<p class="no-collections">No collections loaded. Upload data or use sample data to get started.</p>';
    return;
  }

  collectionsList.innerHTML = '';

  collections.forEach(collection => {
    const collectionItem = document.createElement('div');
    collectionItem.className = 'table-item';

    // Header section
    const collectionHeader = document.createElement('div');
    collectionHeader.className = 'table-header';

    const collectionLeft = document.createElement('div');
    collectionLeft.style.display = 'flex';
    collectionLeft.style.alignItems = 'center';
    collectionLeft.style.gap = '1rem';

    const collectionName = document.createElement('div');
    collectionName.className = 'table-name';
    collectionName.textContent = collection.name;

    const collectionInfo = document.createElement('div');
    collectionInfo.className = 'table-info';
    collectionInfo.textContent = `${collection.document_count} documents, ${collection.fields.length} fields`;

    collectionLeft.appendChild(collectionName);
    collectionLeft.appendChild(collectionInfo);

    const removeButton = document.createElement('button');
    removeButton.className = 'remove-table-button';
    removeButton.innerHTML = '&times;';
    removeButton.title = 'Remove collection';
    removeButton.onclick = () => removeCollection(collection.name);

    collectionHeader.appendChild(collectionLeft);
    collectionHeader.appendChild(removeButton);

    // Fields section
    const collectionFields = document.createElement('div');
    collectionFields.className = 'table-columns';

    collection.fields.forEach(field => {
      const fieldTag = document.createElement('span');
      fieldTag.className = 'column-tag';

      const fieldName = document.createElement('span');
      fieldName.className = 'column-name';
      fieldName.textContent = field.name;

      const fieldType = document.createElement('span');
      fieldType.className = 'column-type';
      const typeEmoji = getTypeEmoji(field.type);
      fieldType.textContent = `${typeEmoji} ${field.type}`;

      fieldTag.appendChild(fieldName);
      fieldTag.appendChild(fieldType);
      collectionFields.appendChild(fieldTag);
    });

    collectionItem.appendChild(collectionHeader);
    collectionItem.appendChild(collectionFields);
    collectionsList.appendChild(collectionItem);
  });
}

// Display upload success
function displayUploadSuccess(response: FileUploadResponse) {
  // Close modal
  const modal = document.getElementById('upload-modal') as HTMLElement;
  modal.style.display = 'none';

  // Show success message
  const successDiv = document.createElement('div');
  successDiv.className = 'success-message';
  successDiv.textContent = `Collection "${response.collection_name}" created successfully with ${response.document_count} documents!`;
  successDiv.style.cssText = `
    background: rgba(40, 167, 69, 0.1);
    border: 1px solid var(--success-color);
    color: var(--success-color);
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
  `;

  const collectionsSection = document.getElementById('collections-section') as HTMLElement;
  collectionsSection.insertBefore(successDiv, collectionsSection.firstChild);

  // Remove success message after 3 seconds
  setTimeout(() => {
    successDiv.remove();
  }, 3000);
}

// Display error
function displayError(message: string) {
  const errorDiv = document.createElement('div');
  errorDiv.className = 'error-message';
  errorDiv.textContent = message;
  
  const resultsContainer = document.getElementById('results-container') as HTMLDivElement;
  resultsContainer.innerHTML = '';
  resultsContainer.appendChild(errorDiv);
  
  const resultsSection = document.getElementById('results-section') as HTMLElement;
  resultsSection.style.display = 'block';
}

// Initialize modal
function initializeModal() {
  const uploadButton = document.getElementById('upload-data-button') as HTMLButtonElement;
  const modal = document.getElementById('upload-modal') as HTMLElement;
  const closeButton = modal.querySelector('.close-modal') as HTMLButtonElement;
  
  // Open modal
  uploadButton.addEventListener('click', () => {
    modal.style.display = 'flex';
  });
  
  // Close modal
  closeButton.addEventListener('click', () => {
    modal.style.display = 'none';
  });
  
  // Close on background click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.style.display = 'none';
    }
  });
  
  // Initialize sample data buttons
  const sampleButtons = modal.querySelectorAll('.sample-button');
  sampleButtons.forEach(button => {
    button.addEventListener('click', async (e) => {
      const sampleType = (e.currentTarget as HTMLElement).dataset.sample;
      await loadSampleData(sampleType!);
    });
  });
}

// Remove collection
async function removeCollection(collectionName: string) {
  if (!confirm(`Are you sure you want to remove the collection "${collectionName}"?`)) {
    return;
  }

  try {
    const response = await fetch(`/api/collection/${collectionName}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error('Failed to remove collection');
    }

    // Reload schema
    await loadDatabaseSchema();

    // Show success message
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.textContent = `Collection "${collectionName}" removed successfully!`;
    successDiv.style.cssText = `
      background: rgba(40, 167, 69, 0.1);
      border: 1px solid var(--success-color);
      color: var(--success-color);
      padding: 1rem;
      border-radius: 8px;
      margin-bottom: 1rem;
    `;

    const collectionsSection = document.getElementById('collections-section') as HTMLElement;
    collectionsSection.insertBefore(successDiv, collectionsSection.firstChild);

    setTimeout(() => {
      successDiv.remove();
    }, 3000);
  } catch (error) {
    displayError(error instanceof Error ? error.message : 'Failed to remove collection');
  }
}

// Get emoji for data type
function getTypeEmoji(type: string): string {
  const upperType = type.toUpperCase();

  // MongoDB/Database types
  if (upperType.includes('INT')) return '🔢';
  if (upperType.includes('REAL') || upperType.includes('FLOAT') || upperType.includes('DOUBLE')) return '💯';
  if (upperType.includes('TEXT') || upperType.includes('CHAR') || upperType.includes('STRING')) return '📝';
  if (upperType.includes('DATE') || upperType.includes('TIME')) return '📅';
  if (upperType.includes('BOOL')) return '✓';
  if (upperType.includes('BLOB')) return '📦';

  // Default
  return '📊';
}

// Load sample data
async function loadSampleData(sampleType: string) {
  try {
    const filename = sampleType === 'users' ? 'users.json' : 'products.csv';
    const response = await fetch(`/sample-data/${filename}`);
    
    if (!response.ok) {
      throw new Error('Failed to load sample data');
    }
    
    const blob = await response.blob();
    const file = new File([blob], filename, { type: blob.type });
    
    // Upload the file
    await handleFileUpload(file);
  } catch (error) {
    displayError(error instanceof Error ? error.message : 'Failed to load sample data');
  }
}
