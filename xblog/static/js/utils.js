function loadPage(urlToLoad, target) {
    $(target).load(urlToLoad, function () {
    });
}

function togglePublish(urlToLoad) {
    alert(urlToLoad);
}

/* 
$(document).ready(function () {
    function loadPage(urlToLoad) {
        $.ajax({
            type: "GET",
            alert(urlToLoad);
            url: urlToLoad,
            data: dataString,
            success: function (returnedData) {
                $('#preview_pane').html(returnedData);
            }
        });
    }
});

*/
