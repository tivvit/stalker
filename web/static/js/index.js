var selectedItems = [];

// todo show and hide controls

const selectable = new Selectable({
    appendTo: document.getElementById("selectable"),
    filter: ".record",
    toggle: true,
    classes: {
        selected: "active",
        selecting: "selecting"
    }
});

selectable.on("selectable.select", function (selected) {
    var pos = selectedItems.indexOf(selected.node.id);
    if (pos === -1) {
        selectedItems.push(selected.node.id);
    }
});

selectable.on("selectable.unselect", function (unselected) {
    var pos = selectedItems.indexOf(unselected.node.id);
    if (pos !== -1) {
        selectedItems.splice(pos);
    }
});

document.getElementById("hide").onclick = function (ev) {
    selectedItems.forEach(function (value) {
        var elem = document.getElementById(value);
        elem.classList.add("hidden");
        elem.classList.remove("active")
    });
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/hide", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status !== 200) {
            console.log(xhr.status, xhr.responseText);
        }
    };
    var data = JSON.stringify({
        "date": document.getElementById("date").value,
        "items": selectedItems
    });
    xhr.send(data);
    selectedItems = [];
};

document.getElementById("clear").onclick = function (ev) {
    clear();
};

function clear() {
    selectedItems.forEach(function (value) {
        var elem = document.getElementById(value);
        elem.classList.remove("active")
    });
    document.querySelectorAll(".active").forEach(function (value) {
        value.classList.remove("active")
    });
    selectedItems = [];
}

document.getElementById("all").onclick = function (ev) {
    selectedItems = [];
    document.querySelectorAll(".record").forEach(function (value) {
        if (value.offsetParent !== null) {
            value.classList.add("active");
            selectedItems.push(value.id);
        }
    });
};

document.getElementById("tag").onclick = function (ev) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/tags", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status !== 200) {
            console.log(xhr.status, xhr.responseText);
        }
    };
    var data = JSON.stringify({
        "date": document.getElementById("date").value,
        "items": selectedItems,
        "tags": document.getElementById("input").value.split(",")
    });
    xhr.send(data);
    clear();
    document.getElementById("input").value = "";
    location.reload();
};

document.getElementById("describe").onclick = function (ev) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/describe", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status !== 200) {
            console.log(xhr.status, xhr.responseText);
        }
    };
    var data = JSON.stringify({
        "date": document.getElementById("date").value,
        "items": selectedItems,
        "description": document.getElementById("input").value
    });
    xhr.send(data);
    clear();
    document.getElementById("input").value = "";
    location.reload();
};


document.getElementById("undescribe").onclick = function (ev) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/undescribe", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status !== 200) {
            console.log(xhr.status, xhr.responseText);
        }
    };
    var data = JSON.stringify({
        "date": document.getElementById("date").value,
        "items": selectedItems
    });
    xhr.send(data);
    clear();
    document.getElementById("input").value = "";
    location.reload();
};


var options = {
    valueNames: [
        'name',
        'start',
        {name: 'duration', attr: 'data-duration'},
        'source',
        'tags'
    ]
};

var hackerList = new List('filter', options);

document.getElementById("lg-filt").addEventListener("change", function (el) {
    var filt = parseFloat(this.value);
    hackerList.filter(function (i) {
        if (isNaN(filt)) {
            return true;
        }
        return i.values().duration > filt;
    });
});


document.getElementById("sm-filt").addEventListener("change", function (el) {
    var filt = parseFloat(this.value);
    hackerList.filter(function (i) {
        if (isNaN(filt)) {
            return true;
        }
        return i.values().duration < filt;
    });
});

document.querySelectorAll(".group_parent").forEach(function (value) {
    value.addEventListener("click", function (el) {
        this.parentElement.parentElement.querySelectorAll(".group").forEach(function (value2) {
            value2.classList.toggle("hidden");
        })
    });
});
