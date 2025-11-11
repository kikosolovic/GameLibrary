from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse

from .forms import RegistrationForm, LoginForm
from .models import Users

def index(request):
    return render(request, 'index.html')

def login_view(request):
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            try:
                user = Users.objects.get(username=username)
                
                if check_password(password, user.password):
                    request.session['user_id'] = user.id
                    request.session['username'] = user.username
                    return redirect('index')
                else:
                    messages.error(request, "Invalid password")
            except Users.DoesNotExist:
                messages.error(request, "User does not exist")
    
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    request.session.flush()
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully. Please log in.")
            return redirect('login')
        else:
            messages.error(request, "Please fix the errors below.")

    else:
        form = RegistrationForm()
    
    return render(request, 'register.html', {'form':form})

def gamecard(request, id=None):
    return render(request, 'gamecard.html')

def search_api(request):
    """
    API endpoint for live search autocomplete
    Returns JSON with matching games
    """
    query = request.GET.get('q', '')
    
    if not query:
        return JsonResponse({'results': []})
    
    games = search_games_by_name(query)

    results = [
        {
            'id': game['id'],
            'title': game['title'],
            'cover_image': game['cover_image'],
            'genre': game.get('genre', 'Game')
        }
        for game in games[:20]
    ]
    
    return JsonResponse({'results': results})

def search_view(request):
    """
    Full search results page (if user clicks "View all results")
    """
    query = request.GET.get('q', '')
    games = search_games_by_name(query)
    
    context = {
        'query': query,
        'games': games,
    }
    
    return render(request, 'search.html', context)


def search_games_by_name(query):
    all_games = [
        {
            'id': 1,
            'title': 'The Legend of Zelda: Breath of the Wild',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Zelda',
            'genre': 'Action-Adventure'
        },
        {
            'id': 2,
            'title': 'Elden Ring',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Elden',
            'genre': 'RPG'
        },
        {
            'id': 3,
            'title': 'Stardew Valley',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Stardew',
            'genre': 'Simulation'
        },
        {
            'id': 4,
            'title': 'Hollow Knight',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Hollow',
            'genre': 'Action'
        },
        {
            'id': 5,
            'title': 'Celeste',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Celeste',
            'genre': 'Platformer'
        },
        {
            'id': 6,
            'title': 'Hades',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Hades',
            'genre': 'Rogue-like'
        },
        {
            'id': 7,
            'title': 'The Witcher 3: Wild Hunt',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Witcher',
            'genre': 'RPG'
        },
        {
            'id': 8,
            'title': 'Red Dead Redemption 2',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=RDR2',
            'genre': 'Action-Adventure'
        },
        {
            'id': 9,
            'title': 'Minecraft',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Minecraft',
            'genre': 'Sandbox'
        },
        {
            'id': 10,
            'title': 'Undertale',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Undertale',
            'genre': 'RPG'
        },
        {
            'id': 11,
            'title': 'Portal 2',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Portal',
            'genre': 'Puzzle'
        },
        {
            'id': 12,
            'title': 'Dark Souls III',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=DarkSouls',
            'genre': 'RPG'
        },
        {
            'id': 13,
            'title': 'Grand Theft Auto V',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=GTA5',
            'genre': 'Action'
        },
        {
            'id': 14,
            'title': 'Terraria',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Terraria',
            'genre': 'Sandbox'
        },
        # Games starting with "blo" for demo
        {
            'id': 15,
            'title': 'Bloodborne',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Bloodborne',
            'genre': 'Action RPG'
        },
        {
            'id': 16,
            'title': 'Blood Bowl 2',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=BloodBowl',
            'genre': 'Sports'
        },
        {
            'id': 17,
            'title': 'Bloons TD 6',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Bloons',
            'genre': 'Tower Defense'
        },
        {
            'id': 18,
            'title': 'Bloodstained: Ritual of the Night',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Bloodstained',
            'genre': 'Metroidvania'
        },
        {
            'id': 19,
            'title': 'Bloober Team Collection',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Bloober',
            'genre': 'Horror'
        },
        {
            'id': 20,
            'title': 'Blockland',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Blockland',
            'genre': 'Sandbox'
        },
        {
            'id': 21,
            'title': 'Bloodroots',
            'cover_image': 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Bloodroots',
            'genre': 'Action'
        },
    ]

    if query:
        filtered_games = [
            game for game in all_games 
            if query.lower() in game['title'].lower()
        ]
        return filtered_games[:20]  
    
    return []