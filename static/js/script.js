

// First Window Transition on Click
document.querySelector('.first-window').addEventListener('click', () => {
    // Add swipe-up animation to the first window
    document.querySelector('.first-window').style.animation = 'swipeUp 0.5s forwards';

    // Wait for the animation to finish before hiding the first window and showing the second window
    setTimeout(() => {
        document.querySelector('.first-window').style.display = 'none';
        document.querySelector('.second-window').style.display = 'block';
    }, 500); // Match the timeout duration to the animation duration
});

// Second Window Navigation
document.querySelectorAll('.second-window .navbar li a').forEach((link) => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        document.querySelectorAll('.second-window .content > div').forEach((div) => {
            div.style.display = 'none';
        });

        const section = e.target.dataset.section;
        document.querySelector(`.${section}`).style.display = 'block';

        document.querySelectorAll('.second-window .navbar li a').forEach((a) => {
            a.classList.remove('active');
        });
        e.target.classList.add('active');
    });
});

// File Upload Transition to Third Window
document.querySelector('#fileInput').addEventListener('change', (e) => {
  const uploadedFile = e.target.files[0];
  const fileType = uploadedFile.type;
  const allowedFileType = 'text/csv';

  if (fileType === allowedFileType) {
    document.querySelector('.second-window').style.display = 'none';
    document.querySelector('.query-window').style.display = 'block';
    document.getElementById('responses').innerHTML = '';
    const columnList = document.getElementById('column-list');
    columnList.innerHTML = '';

    const reader = new FileReader();
    reader.onload = (event) => {
      const csvData = event.target.result;
      const csvRows = csvData.split('\n');
      const columnNames = csvRows[0].split(',');
      const columnTypes = [];

      csvRows[1].split(',').forEach((value, index) => {
        if (!isNaN(parseFloat(value))) {
          columnTypes.push('Number');
        } else if (value.includes('-') || value.includes('/')) {
          columnTypes.push('Date');
        } else {
          columnTypes.push('String');
        }
      });

      columnNames.forEach((columnName, index) => {
        const listItem = document.createElement('LI');
        listItem.textContent = `${columnName} (${columnTypes[index]})`;
        columnList.appendChild(listItem);
      });
    };
    reader.readAsText(uploadedFile);
  } else {
    alert('Unsupported file type. Only .csv files are accepted.');
  }

  // Reset file input value
  e.target.value = '';
});



// Third Window Navigation for Home, About Us, and Help
document.querySelectorAll('.query-window .navbar li a').forEach((link) => {
  link.addEventListener('click', (e) => {
    if (e.target.dataset.section === 'help-content') {
      e.preventDefault();
      document.getElementById('help-popup').style.display = 'block';
    } else if (confirm('Leaving this page will terminate the chat. Are you sure?')) {
      e.preventDefault();
      const section = e.target.dataset.section;
      if (section === 'home') {
        document.querySelector('.query-window').style.display = 'none';
        document.querySelector('.second-window').style.display = 'block';
        document.querySelector('.home-content').style.display = 'block';
        document.querySelector('.about-us-content').style.display = 'none';
        document.querySelector('.help-content').style.display = 'none';
      } else if (section === 'about-us-content') {
        document.querySelector('.query-window').style.display = 'none';
        document.querySelector('.second-window').style.display = 'block';
        document.querySelectorAll('.second-window .content > div').forEach((div) => {
          div.style.display = 'none';
        });
        document.querySelector(`.${section}`).style.display = 'block';
      }
      document.querySelectorAll('.query-window .navbar li a').forEach((a) => {
        a.classList.remove('active');
      });
      e.target.classList.add('active');
    } else {
      e.preventDefault();
    }
  });
});

// Handling Chat Input in Third Window
const responsesContainer = document.getElementById('responses');
const queryInput = document.getElementById('queryInput');
const queryForm = document.getElementById('queryForm'); // Form element

/// Array of end phrases
const end_phrases = ['exit', 'quit', 'bye', 'done', 'finish', 'completed', 'stop', 'end'];

// Function to add user query and bot response placeholders
function addResponse(query) {
    // Display user query
    const userQueryDiv = document.createElement('div');
    userQueryDiv.textContent = query;
    userQueryDiv.classList.add('message', 'user-message');
    responsesContainer.appendChild(userQueryDiv);

    // Display bot response placeholder
    const responseDiv = document.createElement('div');
    responseDiv.textContent = `Generating Visualization.........`;
    responseDiv.classList.add('message', 'bot-response');
    responsesContainer.appendChild(responseDiv);

    // Scroll to the bottom
    responsesContainer.scrollTop = responsesContainer.scrollHeight;

    // Return the bot response div so it can be updated later
    return responseDiv;
}

// Handle form submission
queryForm.addEventListener('submit', async (e) => {
    e.preventDefault(); // Prevent default form submission
    const query = queryInput.value.trim();

    // Check if the query matches any of the end phrases
    if (end_phrases.includes(query.toLowerCase())) {
        // If the user wants to exit, redirect them to the first file upload page
        window.location.href = '/';  // Change this to the actual URL of the file upload page
        return;  // Exit the function early
    }

    if (query) {
        // Add user query and get the placeholder for the bot response
        const botResponseDiv = addResponse(query);

        // Send query to the server
        try {
            const response = await fetch("/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ user_query: query }),
            });

            const result = await response.json();

            // Update the bot response placeholder with the actual server response
            if (result.error_message) {
                botResponseDiv.textContent = `Error: ${result.error_message}`;
            } else if (result.chart_url) {
                botResponseDiv.innerHTML = `
                <h3>Chart Type:</h3>
                <p>${result.chart_type}</p>
                <h3>Columns:</h3>
                <p>${result.chart_cols}</p>
                <h3>Generated Chart:</h3>
                <img src="${result.chart_url}" alt="Generated Chart" style="max-width: 620px; max-height: 498px; width: auto; height: auto;" class="chat-image" onclick="openModal('${result.chart_url}')">
            `;
            } else {
                botResponseDiv.textContent = "No chart generated.";
            }
        } catch (error) {
            console.error("Error:", error);
            botResponseDiv.textContent = "Failed to connect to server.";
        }

        queryInput.value = ""; // Clear input
    }
});

// Modal functionality
function openModal(chartUrl) {
    const modal = document.createElement('div');
    modal.classList.add('modal');
    modal.innerHTML = `
        <div class="modal-content">
            <span class="close-btn" onclick="closeModal()">&times;</span>
            <img src="${chartUrl}" alt="Full-size Chart" class="modal-image">
        </div>
    `;
    document.body.appendChild(modal);
    modal.style.display = 'flex';  // Show the modal (using flex for centering)
}

function closeModal() {
    const modal = document.querySelector('.modal');
    if (modal) {
        modal.style.display = 'none';  // Hide the modal
        modal.remove();  // Remove the modal element from the DOM
    }
}

// Make help popup movable
let helpPopup = document.getElementById('help-popup');
let mousePosition = { x: 0, y: 0 };
let helpPopupPosition = { x: 0, y: 0 };

helpPopup.addEventListener('mousedown', (e) => {
  mousePosition.x = e.clientX;
  mousePosition.y = e.clientY;
  helpPopupPosition.x = helpPopup.offsetLeft;
  helpPopupPosition.y = helpPopup.offsetTop;
  document.addEventListener('mousemove', moveHelpPopup);
  document.addEventListener('mouseup', stopMovingHelpPopup);
});

function moveHelpPopup(e) {
  helpPopup.style.top = (helpPopupPosition.y + (e.clientY - mousePosition.y)) + 'px';
  helpPopup.style.left = (helpPopupPosition.x + (e.clientX - mousePosition.x)) + 'px';
}

function stopMovingHelpPopup() {
  document.removeEventListener('mousemove', moveHelpPopup);
  document.removeEventListener('mouseup', stopMovingHelpPopup);
}

// Close help popup
document.querySelector('.close-help-popup').addEventListener('click', () => {
  document.getElementById('help-popup').style.display = 'none';
});

// Show help popup
document.querySelector('.help-icon').addEventListener('click', () => {
  document.getElementById('help-popup').style.display = 'block';
});
