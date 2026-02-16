document.addEventListener('DOMContentLoaded', function(){
  document.querySelectorAll('pre.payload').forEach(p=>p.style.display='none');
  document.querySelectorAll('button.toggle').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const id = btn.getAttribute('data-id');
      const pre = document.getElementById('payload-'+id);
      if(!pre) return;
      if(pre.style.display === 'none'){
        pre.style.display = 'block';
        btn.textContent = 'Hide payload';
      } else {
        pre.style.display = 'none';
        btn.textContent = 'Show payload';
      }
    });
  });

  const refresh = document.getElementById('refresh');
  if(refresh){
    refresh.addEventListener('click', ()=> location.reload());
  }
});
