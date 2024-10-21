const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('pdf-file');
const fileNameDisplay = document.getElementById('file-name');

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        fileInput.files = files;
        updateFileName(files[0].name);
        submitForm();
    }
});

dropZone.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        updateFileName(fileInput.files[0].name);
        const error = document.getElementById("error");
        if (error) {
            error.innerHTML = '';
        }
        submitForm();
    }
});

function updateFileName(name) {
    fileNameDisplay.textContent = name;
}

function submitForm() {
    const form = document.getElementById('pdf-form');
    const spinner = document.getElementById("spinner");
    const results = document.getElementById("results")

    spinner.style.display = "flex";

    if (results) {
        results.innerHTML = '';
    }

    form.submit();
}

document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("pdf-form");
    const results = document.querySelector('.results');

    form.addEventListener("submit", function (event) {
        if (results) {
            results.innerHTML = '';
        }
    });
});


const loadExcelBtn = document.getElementById('load-excel-btn');
const excelInput = document.getElementById('excel-file');
const excelForm = document.getElementById('excel-form');
const submitExcelBtn = document.getElementById('submit-excel-btn');
const excelError = document.getElementById("excel-error")


if (loadExcelBtn) {
    loadExcelBtn.addEventListener('click', () => {
        excelInput.click();
        excelError.style = 'display: none;'
    });
}

if (excelInput) {
    excelInput.addEventListener('change', () => {
        if (excelInput.files.length > 0) {
            submitExcelBtn.click();
            excelInput.value = "";
        }
    });
}

function copyPartNumbers() {
    let partNumbers = [];
    document.querySelectorAll('.part-numbers-grid li').forEach(function (item) {
        const partNumber = item.innerText.split('Part Number: ')[1].split('\n')[0];
        partNumbers.push(partNumber);
    });

    const partNumbersText = partNumbers.join('\n');
    console.log(partNumbers);
    
    navigator.clipboard.writeText(partNumbersText).then(() => {
        showPopup('Part Numbers copiados al portapapeles');
    }).catch(err => {
        console.error('Error al copiar Part Numbers: ', err);
    });
}

function copyQuantities() {
    let quantities = [];
    document.querySelectorAll('.part-numbers-grid li').forEach(function (item) {
        const quantity = item.innerText.split('Cantidad: ')[1];
        quantities.push(quantity);
    });

    const quantitiesText = quantities.join('\n');
    navigator.clipboard.writeText(quantitiesText).then(() => {
        showPopup('Cantidades copiadas al portapapeles');
    }).catch(err => {
        console.error('Error al copiar Part Numbers: ', err);
    });
}

function showPopup(message) {
    const popup = document.getElementById('copy-popup');
    popup.innerText = message;
    popup.classList.add('show');

    setTimeout(function() {
        popup.classList.remove('show');
    }, 2000);
}