var selectedItems = [];

const selectable = new Selectable({
    filter: ".record",
    toggle: true,
    classes: {
        selected: "active",
        selecting: "selecting"
    }
});

selectable.on("selectable.select", function (selected) {
    var pos = selectedItems.indexOf(selected.node.id);
    if (pos == -1) {
        selectedItems.push(selected.node.id);
    }
    console.log(selectedItems)
});

selectable.on("selectable.unselect", function (unselected) {
    var pos = selectedItems.indexOf(unselected.node.id);
    if (pos != -1) {
        selectedItems.splice(pos);
    }
    console.log(selectedItems)
});

document.getElementById("hide").onclick = function (ev) {
  selectedItems.forEach(function (value) {
      document.getElementById(value).classList.add("hidden");
  });
  selectedItems = [];
};

// document.querySelectorAll(".record").forEach(function (item) {
//     item.onclick = function (elem) {
//         if (selected.indexOf(this.id) != -1) {
//             selected.splice(selected.indexOf(this.id));
//         } else {
//             selected.push(this.id);
//         }
//         this.classList.toggle('active');
//         console.log(selected)
//     };
// });