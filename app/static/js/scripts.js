// const { button } = require("framer-motion/client");

const downloadBtn = document.getElementById('download-btn');
console.log("downloadBtn : ", downloadBtn);
if (downloadBtn) {
    downloadBtn.addEventListener('click', function(event){
        console.log("DOWNLOAD BTN WAS PRESSED");
        window.location.href = '/download-sentiment';
        setTimeout(() => {
            window.location.reload();
        }, 3000);
    })
}
// downloadBtn.addEventListener('click', function(event){
//     console.log("DOWNLOAD BTN WAS PRESSED");
//     window.location.href = '/download-sentiment';
//     setTimeout(() => {
//         window.location.reload();
//     }, 3000);
// })

const downloadBtnCat = document.getElementById('download-btn-category');
console.log("downloadBtnCat : ", downloadBtnCat);
if (downloadBtnCat) {
    downloadBtnCat.addEventListener('click', function(event){
        console.log("DOWNLOAD BTN WAS PRESSED");
        window.location.href = '/download-category';
        setTimeout(() => {
            window.location.reload();
        }, 3000);
    })
}
// downloadBtnCat.addEventListener('click', function(event){
//     console.log("DOWNLOAD BTN WAS PRESSED");
//     window.location.href = '/download-category';
//     setTimeout(() => {
//         window.location.reload();
//     }, 3000);
// })


//Remove all flash on click
function removeAllFlash() {
    const element = document.getElementById('flash-container');
    element.remove();
    window.location.href = '/';
    window.location.reload();
}


function toggleInfo(documentId) {
    // Get all document info divs
    const infoDivs = document.querySelectorAll('div[id^="info-"]');
    const infoBtn = document.querySelectorAll('button[id^="btn-"]');

    // Iterate through each info div
    infoDivs.forEach(div => {
        // Check if the div corresponds to the selected document
        if (div.id === 'info-' + documentId) {
            // Set the display to 'block' for the selected document info
            div.style.display = 'block';
        } else {
            // Hide all other document infos
            div.style.display = 'none';
        }
    });
    // Iterate through each info btn
    infoBtn.forEach(button => {
        console.log('--------');
        console.log(button);
        console.log('--------');
        // Check if the div corresponds to the selected document
        if (button.id === 'btn-' + documentId) {
            console.log('Button FIND')
            // Set the display to 'block' for the selected document info
            // button.style.display = 'block';
            button.classList.add("document-btn-active")
        } else {
            console.log("WRONG button")
            // Hide all other document infos
            // button.style.display = 'none';
            button.classList.remove("document-btn-active")
        }
    });
}






// ai help
// Function to display flash messages
function displayFlashMessages(messages) {
    const flashContainer = document.getElementById('flash-container');
    const flashWrapper = document.getElementById('flash-wrapper');
    // flashContainer.innerHTML = ''; // Clear existing messages
    flashWrapper.innerHTML = ''; // Clear existing messages
    flashContainer.style.display = 'block';

    messages.forEach(message => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('warning');
        messageDiv.innerText = message;
        flashWrapper.appendChild(messageDiv);
    });
}





// function handleCreateNewCategoryButtonClick(key, data) {
//     console.log("inside handleCreateNewCategoryButtonClick -------<");
//     console.log(key);
//     console.log(data);
//     console.log("inside handleCreateNewCategoryButtonClick ------->");
// }


// handleShowDocumentsButtonClick
function handleShowDocumentsButtonClick(key) {
    fetch(`/get_category_data?key=${encodeURIComponent(key)}`)
    .then(response => response.json())
    .then(data => {
        // Process and display the data
        console.log(data);
        console.log(key);
        // You can update your page to display the data here


        let htmlContent = `<div>`
        htmlContent += `<h4>Записи яким запропонована категорія "${key}":</h4>`;


        data.forEach(doc => {
            // console.log(doc)
            htmlContent += `
                <div class="detail-view-document">
                    <p><strong>Нинішня категорія:</strong> ${doc.category}</p>
                    <p><strong>Назва файлу:</strong> ${doc.file_name}</p>
                    <p><strong>Транскрипція:</strong> ${doc.transcription}</p>
                    <p><strong>Дата опрацювання файлу:</strong> ${doc.timestamp}</p>
                </div>
            `;
        });

        // wrapper for buttons:
        htmlContent += `<div class="wrp-category-btn">`;



        // button to create new category in db
        htmlContent += `
        <div>
            <button
                class="create-category-btn"
                data-key="${key}"
            >
                Створити нову категорію: ${key}
            </button>
        </div>
        `;

        // button for abandon new category
        htmlContent += `
        <div>
            <button
                class="abandon-category-btn"
                data-key="${key}"
            >
                Відмовитись від категорії: ${key}
            </button>
        </div>
        `;

        htmlContent += `</div>`;

        htmlContent += `</div>`;

        $('#detail-view').html(htmlContent);

        document.querySelector('.create-category-btn').addEventListener('click', function(event) {
            handleCreateNewCategoryButtonClick(event, key, data);
        });
        document.querySelector('.abandon-category-btn').addEventListener('click', function(event) {
            handleAbandonNewCategoryButtonClick(event, key, data);
        });

    })
    .catch(error => console.error('Error fetching data:', error));
}

function handleAbandonNewCategoryButtonClick(event, key, data) {
    console.log("inside handleAbandonNewCategoryButtonClick -------<");
    console.log(key);
    console.log(data);
    console.log("inside handleAbandonNewCategoryButtonClick ------->");
    fetch(`/abandon_category?key=${encodeURIComponent(key)}`)
    .then(response => response.json())
    .then(data => {
        console.log(`data = ${data}`);
        const is_successfully = data.is_successfully;
        const text = data.text;

        console.log(`is_successfully : ${is_successfully}`)
        console.log(`text : ${text}`)

        if (is_successfully) {
            console.log("YESSS!");
            
            const categoryButton = document.querySelector(`.category-button[data-key="${key}"]`);
            if (categoryButton) {
                categoryButton.parentNode.removeChild(categoryButton);
            }

            // Remove the detail view for the category
            const detailView = document.getElementById('detail-view');
            if (detailView) {
                detailView.innerHTML = `${text}` // Alternatively, you can fade out or transition this removal
            }

        }
    })
}


function handleCreateNewCategoryButtonClick(event, key, data) {
    console.log("inside handleCreateNewCategoryButtonClick -------<");
    console.log(key);
    console.log(data);
    console.log("inside handleCreateNewCategoryButtonClick ------->");
    fetch(`/create_new_category?key=${encodeURIComponent(key)}`)
    .then(response => response.json())
    .then(data => {
        const is_documents_updated = data.is_documents_updated;
        const is_new_category_created = data.is_new_category_created;

        // if(is_documents_updated && is_new_category_created){
        //     console.log("YESSS!");

        // }

        if (is_documents_updated && is_new_category_created) {
            console.log("YESSS!");
            
            // Create new <p> element
            const newElement = document.createElement('p');
            newElement.textContent = "Category created successfully!";
            
            // Replace the button with the new <p> element
            const button = event.target;
            button.parentNode.replaceChild(newElement, button);

            // Remove the category button from the main view
            const categoryButton = document.querySelector(`.category-button[data-key="${key}"]`);
            if (categoryButton) {
                categoryButton.parentNode.removeChild(categoryButton);
            }

            // Remove the detail view for the category
            const detailView = document.getElementById('detail-view');
            if (detailView) {
                detailView.innerHTML = `Нова категорія '${key}' була успішно створена` // Alternatively, you can fade out or transition this removal
            }
        }
        fetch(`/get_category_from_db`)
        .then(response => response.json())
        .then(data => {
            console.log('etch(`/get_category_from_db`)')
            console.log(data)
            console.log('=================--------------')
            exist_category_wrapper_HTML = `<h5>Існуючі категорії:</h5>`
            data.forEach(cat => {
                exist_category_wrapper_HTML += `<p style="margin: 0;">- ${cat}</p>`
            });

            const exist_category_wrapper = document.getElementById('exist-category-wrapper');
            if (exist_category_wrapper) {
                exist_category_wrapper.innerHTML = exist_category_wrapper_HTML;
            }

        })

        // console.log("is_documents_updated");
        // console.log(is_documents_updated);
        // console.log('-----------------');
        // console.log("is_new_category_created");
        // console.log(is_new_category_created);
        // console.log('-----------------');
    })
    .catch(error => {
        console.error('Error fetching data:', error);
    });

}
// function handleShowDocumentsButtonClick(key) {
//     fetch(`/get_category_data?key=${encodeURIComponent(key)}`)
//     .then(response => response.json())
//     .then(data => {
//         // Process and display the data
//         console.log(data);
//         console.log(key);
//         // You can update your page to display the data here

//         let htmlContent = `<h4>Details for: ${key}</h4>`;

//         data.forEach(doc => {
//             // console.log(doc)
//             htmlContent += `
//                 <div class="detail-view-document">
//                     <p><strong>Current Category:</strong> ${doc.category}</p>
//                     <p><strong>File Name:</strong> ${doc.file_name}</p>
//                     <p><strong>Transcription:</strong> ${doc.transcription}</p>
//                     <p><strong>Timestamp:</strong> ${doc.timestamp}</p>
//                 </div>
//             `;
//         });



//         $('#detail-view').html(htmlContent);

//     })
//     .catch(error => console.error('Error fetching data:', error));
// }
// function handleShowDocumentsButtonClick(key) {
//     fetch(`/get_category_data?key=${encodeURIComponent(key)}`)
//     .then(response => response.json())
//     .then(data => {
//         // Process and display the data
//         console.log(data);
//         console.log(key);
//         // You can update your page to display the data here


//         let htmlContent = `<div>`
//         htmlContent += `<h4>Details for: ${key}</h4>`;


//         data.forEach(doc => {
//             // console.log(doc)
//             htmlContent += `
//                 <div class="detail-view-document">
//                     <p><strong>Current Category:</strong> ${doc.category}</p>
//                     <p><strong>File Name:</strong> ${doc.file_name}</p>
//                     <p><strong>Transcription:</strong> ${doc.transcription}</p>
//                     <p><strong>Timestamp:</strong> ${doc.timestamp}</p>
//                 </div>
//             `;
//         });

//         htmlContent += `
//         <div>
//             <button
//                 onClick="handleCreateNewCategoryButtonClick('${key}', ${JSON.stringify(data)})"
//             >
//                 Створити нову категорію: ${key}
//             </button>
//         </div>
//         `;

//         htmlContent += `</div>`;

//         $('#detail-view').html(htmlContent);

//     })
//     .catch(error => console.error('Error fetching data:', error));
// }