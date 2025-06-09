function showPopup() {
  document.getElementById("popup").style.display = "block";
  document.getElementById("overlay").style.display = "block";
}

function hidePopup() {
  document.getElementById("popup").style.display = "none";
  document.getElementById("overlay").style.display = "none";
}

function confirmResignation() {
  const currentDate = new Date();
  const formattedResignationDate = currentDate.toISOString().split('T')[0]; // YYYY-MM-DD

  const lastWorkingDay = new Date();
  lastWorkingDay.setDate(currentDate.getDate() + 60);
  const formattedLastWorkingDay = lastWorkingDay.toISOString().split('T')[0]; // YYYY-MM-DD

  localStorage.setItem('resignationDate', formattedResignationDate);
  localStorage.setItem('lastWorkingDay', formattedLastWorkingDay); // Store only YYYY-MM-DD

  window.location.href = "/submit_resignation/"; // Redirect to the next page
}

// For ResignationForm.html to retrieve and display the dates
window.onload = function() {
  const resignationDate = localStorage.getItem('resignationDate');
  const lastWorkingDay = localStorage.getItem('lastWorkingDay');

  if (resignationDate && document.getElementById('res_date')) {
      document.getElementById('res_date').value = resignationDate;
  }

  if (lastWorkingDay && document.getElementById('last_day')) {
      document.getElementById('last_day').value = lastWorkingDay; // Ensure it is YYYY-MM-DD
  }
};
