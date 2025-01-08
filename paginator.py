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
        card_embed = discord.Embed(title="Card List")
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        user_card_names = [card['card_name'] for card in self.user_cards]

        field_count = 0  # Initialize a counter for the number of fields

        for card in cards[start:end]:
            for user_card in self.user_cards:
                if field_count >= 25:  # Check if the field count exceeds the limit
                    break  # Stop adding fields if limit is reached

                if card['card_name'] in user_card_names:
                    card_embed.add_field(
                        name=f"{user_card['card_name']} - {user_card['card_number']}",
                        value=f"Cost: {user_card['cost']} coins\n[View Card]({user_card['card_url']})\nx{user_card['card_count']}",
                        inline=True
                    )
                    field_count += 1  # Increment the field count
                else:
                    card_embed.add_field(
                        name="???",  # Placeholder for cards the user doesn't have
                        value="This card is not owned by you.",
                        inline=True
                    )
                    field_count += 1  # Increment the field count

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