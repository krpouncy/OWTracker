/* ==========================
   Chart Initialization
========================== */
// Global reference to chart
let winChart = null;

// Load Chart.js from CDN and initialize chart
const scriptElement = document.createElement('script');
scriptElement.src = "https://cdn.jsdelivr.net/npm/chart.js";
scriptElement.onload = () => {
    console.log('Chart.js has been loaded');
    initChart();
};
document.head.appendChild(scriptElement);

function initChart() {
  const ctx = document.getElementById('win-chart');
  if (!ctx) {
    console.warn("No #win-chart element found. Skipping chart init.");
    return;
  }
  winChart = new Chart(ctx.getContext('2d'), {
  type: 'line',
  data: {
    labels: [], // Dynamic labels
    datasets: [
      {
        label: 'Win Probability',
        data: [],
        backgroundColor: 'rgba(52, 152, 219, 0.2)', // Light blue gradient
        borderColor: 'rgba(41, 128, 185, 1)', // Deep blue
        borderWidth: 3,
        pointBackgroundColor: 'rgba(255, 140, 0, 0.9)', // Orange points
        pointBorderColor: 'rgba(255, 215, 0, 1)', // Gold border for points
        pointRadius: 6,
        pointHoverRadius: 8,
        tension: 0.4, // Smooth line
      },
    ],
  },
  options: {
    plugins: {
      legend: {
        labels: {
          color: 'rgba(255, 255, 255, 0.9)', // Off-white text
          font: {
            size: 14,
            weight: '500',
          },
        },
      },
      annotation: {
        annotations: {
          thresholdLine: {
            type: 'line',
            mode: 'horizontal',
            scaleID: 'y',
            value: 55, // Dynamic threshold value
            borderColor: 'rgba(231, 76, 60, 1)', // Bright red
            borderWidth: 2,
            borderDash: [6, 6], // Dashed line
            label: {
              enabled: true,
              content: 'Threshold',
              position: 'start',
              backgroundColor: 'rgba(44, 62, 80, 0.8)', // Dark glossy background
              color: 'white',
              font: {
                size: 12,
                weight: 'bold',
              },
              padding: 6,
            },
          },
        },
      },
      tooltip: {
        backgroundColor: 'rgba(44, 62, 80, 0.9)', // Dark glossy tooltip
        titleColor: 'white',
        bodyColor: 'rgba(200, 200, 200, 0.9)', // Light gray
        borderColor: 'rgba(41, 128, 185, 1)', // Deep blue
        borderWidth: 1,
        padding: 12,
      },
    },
    scales: {
      x: {
        ticks: {
          color: 'rgba(255, 255, 255, 0.8)', // Soft white
          font: {
            size: 12,
          },
        },
        title: {
          display: true,
          text: 'Events',
          color: 'rgba(255, 255, 255, 0.8)',
          font: {
            size: 14,
            weight: '600',
          },
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)', // Subtle grid lines
        },
      },
      y: {
        ticks: {
          color: 'rgba(255, 255, 255, 0.8)',
          font: {
            size: 12,
          },
        },
        title: {
          display: true,
          text: 'Win Probability (%)',
          color: 'rgba(255, 255, 255, 0.8)',
          font: {
            size: 14,
            weight: '600',
          },
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
        min: 0,
        max: 100,
      },
    },
    responsive: true,
    // maintainAspectRatio: false
  },
});

}

/* ==========================
   Socket.IO Events (Core)

   These are triggered by the UserEventHandler class using the socket_object.
========================== */
socket.on('update_chart', (win_probability) => {
  // data is expected to be a float value between 0 and 1
  console.log('Received update_chart event:', win_probability);
  if (winChart && win_probability) {
    const probability = (win_probability * 100).toFixed(1);
    winChart.data.labels.push(`Event ${winChart.data.labels.length + 1}`);
    winChart.data.datasets[0].data.push(probability);
    winChart.update();
  }
});

socket.on('reset_chart', () => {
  console.log('Chart reset event received');
  if (winChart) {
    winChart.data.labels = [];
    winChart.data.datasets[0].data = [];
    winChart.update();
  }
});