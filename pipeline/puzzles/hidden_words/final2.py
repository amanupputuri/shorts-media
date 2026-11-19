import ws2, audio
vo=[(ws2.ws.VOICE_DIR+f'/l{li:02d}.wav',t) for li,t in ws2.VOICE]
L=audio.build(ws2.TOTAL, ws2.events(), 'mix2.wav', vo)
print(ws2.TOTAL, L)
