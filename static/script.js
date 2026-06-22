document
.getElementById("generateBtn")
.addEventListener("click", async () => {

    const file =
    document.getElementById("excelFile")
    .files[0];

    if(!file){

        alert("Select Excel File");
        return;
    }

    const formData = new FormData();

    formData.append("file", file);

    const status =
    document.getElementById("status");

    status.innerHTML =
    "Generating PDF...";

    try{

        const response =
        await fetch(
            "http://localhost:5000/generate_qr",
            {
                method:"POST",
                body:formData
            }
        );

        const blob =
        await response.blob();

        const url =
        window.URL.createObjectURL(blob);

        const a =
        document.createElement("a");

        a.href = url;

        a.download =
        "imei_labels.pdf";

        a.click();

        status.innerHTML =
        "PDF Downloaded";
        
        formData = new FormData()
    }
    catch(err){

        status.innerHTML =
        err.message;
    }
});