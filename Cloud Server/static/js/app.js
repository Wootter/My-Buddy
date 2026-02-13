let lightmode = localStorage.getItem('lightmode')

const toggleButton = document.getElementById('toggle-btn')
const sidebar = document.getElementById('sidebar')
const password = document.getElementById('password')
const eyeOpen = document.getElementById('eye-open')
const eyeClose = document.getElementById('eye-closed')
const themeSwitch = document.getElementById('theme-switch')

const enableLightmode = () => {
  document.documentElement.classList.add('lightmode')
  document.body.classList.add('lightmode')
  localStorage.setItem('lightmode', 'active')
}

const disableLightmode = () => {
  document.documentElement.classList.remove('lightmode')
  document.body.classList.remove('lightmode')
  localStorage.setItem('lightmode', null)
}

// Apply theme on page load
if(lightmode === 'active') enableLightmode()

// Theme switch event listener - check actual DOM state, not cached value
if(themeSwitch) {
  themeSwitch.addEventListener('click', () => {
    const isCurrentlyLight = document.body.classList.contains('lightmode')
    isCurrentlyLight ? disableLightmode() : enableLightmode()
  })
}

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
    eyeClose.style.display = 'none'
    eyeOpen.style.display = 'block'
  } else {
    password.type = 'password'
    eyeOpen.style.display = 'none'
    eyeClose.style.display = 'block'
  }
}
