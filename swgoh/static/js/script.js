function draw_charts(canvas_id, label, dataset) {

	var labels = []
	var data = []

	var events = dataset.events
	for (var index in events) {
		entry = events[index];
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

$(document).ready(function() {
	// Display 50 entries by default in dataTables
	$.fn.dataTable.defaults['iDisplayLength'] = 50;
});
