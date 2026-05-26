import pygame
from csv import reader
from settings import tile_size

#uses csv files from tiled editor to create maps
def import_csv_layout(path):
    terrain_map = []
    with open(path) as map:
        level = reader(map, delimiter = ',')
        for row in level:
            terrain_map.append(list(row))
        return terrain_map

def import_cut_graphics(path):
    surface = pygame.image.load(path).convert_alpha()
    
    #use 32 because that is the size of the tiles 
    asset_size = 32 
    tile_num_x = int(surface.get_size()[0] / asset_size)
    tile_num_y = int(surface.get_size()[1] / asset_size)

    cut_tiles = []
    for row in range(tile_num_y):
        for col in range(tile_num_x):
            x = col * asset_size
            y = row * asset_size
            new_surf = pygame.Surface((asset_size, asset_size), flags = pygame.SRCALPHA)
            new_surf.blit(surface, (0, 0), pygame.Rect(x, y, asset_size, asset_size))
            
            scaled_surf = pygame.transform.scale(new_surf, (tile_size, tile_size))
            cut_tiles.append(scaled_surf)
    return cut_tiles


def import_sprite_list(path):
    surface = pygame.image.load(path).convert_alpha()   

    unit_w = 16
    unit_h = surface.get_size()[1] 
     
    tile_num_x = int(surface.get_size()[0] // unit_w)
    list_of_frames = []
     
    for col in range(tile_num_x):
        x = col * unit_w
        temp_surf = pygame.Surface((unit_w, unit_h), flags = pygame.SRCALPHA)
        temp_surf.blit(surface, (0, 0), pygame.Rect(x, 0, unit_w, unit_h))
        
        #checks if the frame actually has artwork in it
        #if the width is greater than 0, it means it's not a blank transparent box
        if temp_surf.get_bounding_rect().width > 0:
            scaled_surf = pygame.transform.scale(temp_surf, (32, unit_h * 2))
            list_of_frames.append(scaled_surf)
    
    return list_of_frames


def import_npc_sprites(path):
    surface = pygame.image.load(path).convert_alpha()
    
    # Your Canvas size is 96x96
    unit_w = 96
    unit_h = 96
    y = 0 
     
    tile_num_x = int(surface.get_size()[0] // unit_w)
    list_of_frames = []
     
    for col in range(tile_num_x):
        x = col * unit_w
        temp_surf = pygame.Surface((unit_w, unit_h), flags = pygame.SRCALPHA)
        # Grab the 96x96 area
        temp_surf.blit(surface, (0, 0), pygame.Rect(x, y, unit_w, unit_h))
        

        scaled_surf = pygame.transform.scale(temp_surf, (3* tile_size, 3*tile_size))
        list_of_frames.append(scaled_surf)
        
    return list_of_frames