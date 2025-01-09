import discord
from external_defs import ExternalDefs

color_mapping = {
    "RED": discord.Color.red(),
    "GREEN": discord.Color.green(),
    "BLUE": discord.Color.blue(),
    "PURPLE": discord.Color.purple(),
    "RAINBOW": discord.Color.from_rgb(255, 0, 255),  # Custom color for rainbow
    "YELLOW": discord.Color.from_rgb(255, 255, 0),  # Custom color for yellow
    "ORANGE": discord.Color.from_rgb(255, 165, 0),  # Custom color for orange
}


class Paginator:
    def __init__(self, cards, guild, user_cards, items_per_page=5 ):
        self.cards = cards
        self.items_per_page = items_per_page
        self.total_pages = (len(cards) + items_per_page - 1) // items_per_page
        self.current_page = 0
        self.guild = guild
        self.user_cards = user_cards





    def get_embed(self):
        cards = ExternalDefs.load_cards('cards.json')
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        user_card_names = [card['card_name'] for card in self.user_cards]
        user_card_count = {card['card_name']: card['card_count'] for card in self.user_cards}  # Create a dictionary for easy access
        card_embed = discord.Embed(title=f"Card List\nTotal Cards: x{sum(user_card_count.values())}", colour=discord.Colour.brand_green())


        field_count = 0  # Initialize a counter for the number of fields
        embed_placeholder_count = 0
        embed_card_count = 0

        obtained_cards = []
        placeholder_cards = []


        for card in cards[start:end]:
            if (embed_placeholder_count + embed_card_count) >= 25:
                break
            if card['card_name'] in user_card_names:
                embed_card_count += 1
                card["card_count"] = user_card_count[card['card_name']]
                card["order"] = int(card['card_number'].lstrip('#'))
                obtained_cards.append(card)
            else:
                embed_placeholder_count += 1
                placeholder_card = {
                    "card_name": "???",
                    "card_number": card['card_number'],
                    "card_url": "???",
                    "card_color": "???",
                    "card_count": 0,
                    "cost": card['cost'],
                    "order" : int(card['card_number'].lstrip('#'))
                    
                }
                placeholder_cards.append(placeholder_card)

        combined_cards_dict = placeholder_cards + obtained_cards

        sorted_dict = sorted(combined_cards_dict, key=lambda x: x["order"])

        for card in sorted_dict:
            if card['card_url'] == "???":
                card_embed.add_field(
                    name=f"{card['card_name']} - {card['card_number']}",
                    value=f"Cost: {card['cost']} coins",
                    inline=True
                )
            else:
                card_embed.add_field(
                    name=f"{card['card_name']} - {card['card_number']}",
                    value=f"Cost: {card['cost']} coins\n[View Card]({card['card_url']})\nx{card['card_count']}",
                    inline=True
                )
            
        return card_embed

    def get_view(self):
        view = discord.ui.View()

        async def previous_callback(interaction):
            self.current_page -= 1
            await self.update(interaction)

        async def next_callback(interaction):
            self.current_page += 1
            await self.update(interaction)

        if self.current_page > 0:
            previous_button = discord.ui.Button(label="Previous", style=discord.ButtonStyle.primary, custom_id="previous")
            previous_button.callback = previous_callback  # Set the callback for the previous button
            view.add_item(previous_button)

        if self.current_page < self.total_pages - 1:
            next_button = discord.ui.Button(label="Next", style=discord.ButtonStyle.primary, custom_id="next")
            next_button.callback = next_callback  # Set the callback for the next button
            view.add_item(next_button)

        return view  # Ensure the view is returned

    async def update(self, interaction):
        embed = self.get_embed()
        view = self.get_view()
        await interaction.response.edit_message(embed=embed, view=view)