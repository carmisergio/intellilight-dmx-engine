import pygame, sys, random
from pygame.locals import QUIT 
import array
import json

# CONFIG VARIABLES #
WINDOWWIDTH = 500
WINDOWHEIGHT = 400
FPS = 500
BOARDWIDTH = 5
BOARDHEIGHT = 4
FILEPATH = "files\lightdata.json"
# CONFIG VARIABLES #

BOXWIDTH = WINDOWWIDTH / BOARDWIDTH
BOXHEIGHT = WINDOWHEIGHT / BOARDHEIGHT

#Main function
def main():
    global FPSCLOCK, DISPLAYSURF

    #Initialize pygame + pygame clock
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    pygame.display.set_caption("Light Output Visualizer")
    font = pygame.font.Font(None, 25)

    #Generate array with 512 0s
    lightdata = []
    for _ in range(0, 512):
        lightdata.append(0)

    while True: #Main loop
        #Fill window
        DISPLAYSURF.fill((0, 0, 0))
        
        #Handle pygame events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
        
        #Try to open and parse json
        with open(FILEPATH) as f:
            try:
                data = json.load(f)
                lightdata = data["data"]
            except:
                print("An exception occurred")
            
        i = 0
        #Render light values
        for y, _ in enumerate(range(0, BOARDHEIGHT)): #For every line
            for x, _ in enumerate(range(0, BOARDWIDTH)): #For every square in that line
                
                data = lightdata[i]
                
                #Make sure maximum value is 255
                if data > 255:
                    data = 255
                
                #Draw
                pygame.draw.rect(DISPLAYSURF, (data, data, data), (x * BOXWIDTH, y * BOXHEIGHT, BOXWIDTH, BOXHEIGHT))
                text = font.render(str(i + 1), True, (255, 0, 0))
                DISPLAYSURF.blit(text, (x * BOXWIDTH, y * BOXHEIGHT))
                
                i += 1 #Increment counter


        #Update display and regulate FPS
        pygame.display.update()
        FPSCLOCK.tick(FPS)

if __name__ == "__main__":
    main()