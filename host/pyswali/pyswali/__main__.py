import asyncio
from .gateway import gateway

async def main():
    gw = gateway()
    await gw.connect()
    await gw.scan()
    lights = [x for x in gw.get_lights() if x.is_enabled()]
    print('lights:')
    for light in lights:
        print('  {:<16} - {} - {}'.format(light.get_name(), light.get_state(), light.get_group()))

    print('groups:')
    for group in gw.get_groups():
        print('  {}'.format(group))
        
    await gw.start_update()
    
    await asyncio.sleep(10.0) 

    await gw.close()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
