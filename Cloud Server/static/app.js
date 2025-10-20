const toggleButton = document.getElementById('toggle-btn')
const sidebar = document.getElementById('sidebar')
const password = document.getElementById('password')
const eyeOpen = document.getElementById('eye-open')
const eyeClose = document.getElementById('eye-closed')

function toggleSidebar(){
  sidebar.classList.toggle('close')
  toggleButton.classList.toggle('rotate')

  closeAllSubMenus()
}

function toggleSubMenu(button){

  if(!button.nextElementSibling.classList.contains('show')){
    closeAllSubMenus()
  }

  button.nextElementSibling.classList.toggle('show')
  button.classList.toggle('rotate')

  if(sidebar.classList.contains('close')){
    sidebar.classList.toggle('close')
    toggleButton.classList.toggle('rotate')
  }
}

function closeAllSubMenus(){
  Array.from(sidebar.getElementsByClassName('show')).forEach(ul => {
    ul.classList.remove('show')
    ul.previousElementSibling.classList.remove('rotate')
  })
}

function togglePasswordVisibility(){
  if(password.type === 'password'){
    password.type = 'text'
    eyeOpen.style.display = 'none'
    eyeClose.style.display = 'block'
  } else {
    password.type = 'password'
    eyeOpen.style.display = 'block'
    eyeClose.style.display = 'none'
  }
}
