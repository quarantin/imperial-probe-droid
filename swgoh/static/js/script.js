function draw_charts(canvas_id, label, dataset) {

	var labels = []
	var data = []

	for (var index in dataset) {
		entry = dataset[index];
		labels.push(entry.label);
		data.push(entry.value);
	}

	var ctx = document.getElementById(canvas_id).getContext('2d');
	var myChart = new Chart(ctx, {
		type: 'bar',
		data: {
			labels: labels,
			datasets: [{
				label: label,
				data: data,
				backgroundColor: 'rgba(54, 162, 235, 0.2)',
				borderColor: 'rgba(54, 162, 235, 1)',
				borderWidth: 1
			}]
		},
		options: {
			scales: {
				yAxes: [{
					ticks: {
						beginAtZero: true
					}
				}]
			}
		}
	});
}

function draw_table(container_id, dataset) {

	var tbody = $('#' + container_id).find('tbody')

	tbody.empty();

	for (var i = 0; i < dataset.length; i++) {

		var entry = dataset[i];

		var td0 = document.createElement('td');
		td0.innerHTML = i + 1;

		var td1 = document.createElement('td');
		td1.innerHTML = entry.label;

		var td2 = document.createElement('td');
		td2.innerHTML = entry.value;

		var tr = document.createElement('tr');
		tr.appendChild(td0);
		tr.appendChild(td1);
		tr.appendChild(td2);
		tbody.append(tr);
	}
}

$(document).ready(function() {
	// Display 50 entries by default in dataTables
	$.fn.dataTable.defaults['iDisplayLength'] = 50;
});
