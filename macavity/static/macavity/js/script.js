const menuBtn = document.querySelector('.menu-btn');
const menu = document.querySelector('.menu');
const content = document.querySelector('.content');
const nav = document.querySelector('.topnav');
const nav_search = document.querySelector('.topnav_search');

const like_btn = document.getElementById('like')
const dislike_btn = document.getElementById('dislike')

const cat_btn = document.getElementById('cat_btn')
const cats = document.querySelector('.cats_in_player')

const description_btn = document.getElementById('description_btn')
const description_in_player = document.querySelector('.description_in_player')

const add_to_playlist_btn = document.getElementById('add_to_playlist')
const playlists_list = document.querySelector('.playlists_list')
const playlists_list_replace = document.querySelector('.playlists_list_replace')

const change_video_btn = document.getElementById('change_video_btn')

const subscribe_btn = document.getElementById('subscribe_btn')

const subscribe_video_btn = document.getElementById('subscribe_video_btn')

const add_cat_btn = document.getElementById('add_cat_btn')

//MENU SCRIPT
menuBtn.addEventListener('click', function(e) {
  e.preventDefault();
  menu.classList.toggle('menu_active');
  if (content != null){
    content.classList.toggle('content_active')
}
  nav.classList.toggle('topnav-active');
});

if(cat_btn){
  cat_btn.onclick = function(e){
    e.preventDefault();
    cats.classList.toggle('cats_in_player-active')
  }
  description_btn.onclick = function(e){
    e.preventDefault();
    description_in_player.classList.toggle('description_in_player-active')
  }
}
if(change_video_btn){
    change_video_btn.onclick = function(e){
      e.preventDefault();
      let redirrect_url = document.getElementById('change_video_redirrect_url').value
      window.location.href=redirrect_url
    }
  }

//POST add cat ajax
if(add_cat_btn){
  add_cat_btn.onclick = function(e){
    e.preventDefault();
    let csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
    let url = window.location.href;
    let input = document.getElementById('add_cat_form').add_cat_name.value
    input = encodeURIComponent(input)

    let data = JSON.stringify({
      cat_name: input,
      request: 'add_comment',
    })

    let xhr = new XMLHttpRequest();
    
    xhr.open('POST', url, true)
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest')
    xhr.setRequestHeader('X-CSRFToken', csrf)
    xhr.onreadystatechange = function(){
      if(xhr.readyState == 4 && xhr.status == 200){
        let new_data=xhr.responseText;
        let jsonResponse = JSON.parse(new_data);
        
        document.getElementById('id_cat').innerHTML = jsonResponse["html"];
        document.getElementById('add_cat_form').reset();
      }
    }
    xhr.send(data)
    
  }
}

//GET USER PLAYLISTS AJAX
if(add_to_playlist_btn){
  add_to_playlist_btn.onclick = function(e){
    e.preventDefault();

    function myclick(click){
      if (!(click.target === playlists_list || playlists_list.contains(click.target))){
        document.removeEventListener("click", myclick, true)
        if(playlists_list.classList == 'playlists_list playlists_list-active'){
          click.preventDefault()
          click.stopImmediatePropagation()
          playlists_list.classList.toggle('playlists_list-active')
        }
      }
    }

    document.addEventListener("click", myclick, true)

    let xhr = new XMLHttpRequest();
    let url = window.location.href

    xhr.open('GET', url, true)
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest')
    xhr.setRequestHeader('get-requets', 'user-playlists')
    xhr.onreadystatechange = function(){
      if(xhr.readyState == 4 && xhr.status == 200){
        let new_data=xhr.responseText;
        let jsonResponse = JSON.parse(new_data);
        
        playlists_list_replace.innerHTML = jsonResponse["html"];
        playlists_list.classList.toggle('playlists_list-active')
      }
    }
    xhr.send()
    
  }
}

//POST COMMENT AJAX
if (document.forms['comment_form']){
  document.forms['comment_form'].onsubmit= function(e){
    e.preventDefault();
    let csrf = document.forms['comment_form'].csrfmiddlewaretoken.value
    let input = document.forms['comment_form'].comment_text.value
    input = encodeURIComponent(input)
    let video_pk = document.getElementById("video_comment").value
    let url = window.location.href

    let data =JSON.stringify({
      comment_text: input,
      video_comment: video_pk,
      request: 'add_comment'
    })

    let xhr = new XMLHttpRequest();
    
    xhr.open('POST', url, true)
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest')
    xhr.setRequestHeader('X-CSRFToken', csrf)
    xhr.onreadystatechange = function(){
      if(xhr.readyState == 4 && xhr.status == 200){
        let new_data=xhr.responseText;
        let jsonResponse = JSON.parse(new_data);
        document.getElementById("comments").innerHTML = jsonResponse["html"];
        document['comment_form'].reset();
      }
    }

    xhr.send(data)
  }
}
// ADD/REMOVE LIKE AJAX
if(like_btn){
  like_btn.onclick = function(e){
    e.preventDefault();

    let csrf = document.forms['comment_form'].csrfmiddlewaretoken.value
    let video_pk = document.getElementById("video_comment").value
    let url = window.location.href

    let data =JSON.stringify({
      video_like: video_pk,
      request: 'like'
    })

    let xhr = new XMLHttpRequest();
    
    xhr.open('POST', url, true)
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest')
    xhr.setRequestHeader('X-CSRFToken', csrf)
    xhr.onreadystatechange = function(){
      if(xhr.readyState == 4 && xhr.status == 200){
        let new_data=xhr.responseText;
        let jsonResponse = JSON.parse(new_data);
        document.getElementById("likes_value").innerHTML = jsonResponse["likes"];
        if (typeof jsonResponse["dislikes"] !== 'undefined'){
        document.getElementById("dislikes_value").innerHTML = jsonResponse["dislikes"];
        }
      }
    }

    xhr.send(data)
  }
}
// ADD/REMOVE DISLIKE AJAX
if (dislike_btn){
  dislike_btn.onclick = function(e){
    e.preventDefault();
    let csrf = document.forms['comment_form'].csrfmiddlewaretoken.value
    let video_pk = document.getElementById("video_comment").value
    let url = window.location.href

    let data =JSON.stringify({
      video_dislike: video_pk,
      request: 'dislike'
    })

    let xhr = new XMLHttpRequest();
    
    xhr.open('POST', url, true)
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest')
    xhr.setRequestHeader('X-CSRFToken', csrf)
    xhr.onreadystatechange = function(){
      if(xhr.readyState == 4 && xhr.status == 200){
        let new_data=xhr.responseText;
        let jsonResponse = JSON.parse(new_data);
        document.getElementById("dislikes_value").innerHTML = jsonResponse["dislikes"];
        if (typeof jsonResponse["likes"] !== 'undefined'){
        document.getElementById("likes_value").innerHTML = jsonResponse["likes"];
        }
      }
    }

    xhr.send(data)
  }
}
//POST add video to a playlist
function add_video_to_playlist(pk){
  let csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
  let playlist_pk = pk
  let url = window.location.href

  let data =JSON.stringify({
    playlist_pk: playlist_pk,
    request: 'add_video_to_playlist'
  })

  let xhr = new XMLHttpRequest();
  
  xhr.open('POST', url, true)
  xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest')
  xhr.setRequestHeader('X-CSRFToken', csrf)
  xhr.onreadystatechange = function(){
    if(xhr.readyState == 4 && xhr.status == 200){
      playlists_list.classList.toggle('playlists_list-active');
      document.getElementById
    }
  }

  xhr.send(data)
}


//POST add playlist via ajax
if(document.forms['add_playlist_form']){
  document.forms['add_playlist_form'].onsubmit= function(e){
    e.preventDefault();
    e.stopImmediatePropagation();
    const csrf = document.forms['add_playlist_form'].csrfmiddlewaretoken.value
    let input = document.forms['add_playlist_form'].add_playlist_name.value
    input = encodeURIComponent(input)
    let url = document.URL

    let data =JSON.stringify({
      playlist_name: input,
      request: 'add_playlist'
    })

    let xhr = new XMLHttpRequest();
    
    xhr.open('POST', url, true)
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest')
    xhr.setRequestHeader('X-CSRFToken', csrf)
    xhr.onreadystatechange = function(){
      if(xhr.readyState == 4 && xhr.status == 200){
        let new_data=xhr.responseText;
        let jsonResponse = JSON.parse(new_data);
        playlists_list_replace.innerHTML = jsonResponse["html"];
        
        document['add_playlist_form'].reset();
      }
    }
    xhr.send(data)
  }
}
//subscribe
if(subscribe_btn){
  subscribe_btn.onclick = function(e){
    e.preventDefault();

    let xhr = new XMLHttpRequest();
    let url = window.location.href

    xhr.open('GET', url, true)
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest')
    xhr.setRequestHeader('action', 'subscribe')

    xhr.onreadystatechange = function(){
      if(xhr.readyState == 4 && xhr.status == 200){
        let new_data=xhr.responseText;
        let jsonResponse = JSON.parse(new_data);

        document.getElementById("sub_counter").innerHTML = jsonResponse["sub_num"];
      }
    }
    xhr.send()
    
  }
}


//subscribe from video_player
if(subscribe_video_btn){
  subscribe_video_btn.onclick = function(e){
    e.preventDefault();

    let url = window.location.href
    let xhr = new XMLHttpRequest();

    xhr.open('GET', url, true)
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest')
    xhr.setRequestHeader('get-requets', 'subscribe')

    xhr.onreadystatechange = function(){
      if(xhr.readyState == 4 && xhr.status == 200){
        let new_data=xhr.responseText;
        let jsonResponse = JSON.parse(new_data);

        document.getElementById("sub_counter").innerHTML = jsonResponse["sub_num"];
      }
    }
    xhr.send()
    
  }
}